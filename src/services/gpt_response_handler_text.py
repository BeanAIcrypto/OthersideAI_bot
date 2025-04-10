import os
import asyncio
from langchain_openai import ChatOpenAI
from openai import OpenAIError
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from src.services.count_token import count_tokens, count_total_tokens
import logging
from db.dbworker import get_user_limit, update_user_limit
from src.bot.bot_messages import MESSAGES, MESSAGES_ERROR
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_GPT4 = "gpt-4o"
API_KEY = os.getenv("GPT_SECRET_KEY_FASOLKAAI")

embeddings = OpenAIEmbeddings(
    openai_api_key=API_KEY,
    model="text-embedding-ada-002"
)
logger.info("Инициализация OpenAIEmbeddings")

try:
    retriever = FAISS.load_local(
        "faiss_index_US",
        embeddings,
        allow_dangerous_deserialization=True
    ).as_retriever(
        k=4,
        search_type="similarity",
        search_kwargs={'k': 4},
        fetch_k=50
    )
    logger.info("FAISS индекс загружен успешно.")
except Exception as e:
    logger.error(f"Ошибка загрузки FAISS индекса: {e}")
    raise


async def create_retriever_chain(llm, prompt_text):
    """Создание цепочки ретривера"""
    try:
        logger.info("Создание цепочки ретривера.")

        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            SystemMessagePromptTemplate.from_template(prompt_text),
            HumanMessagePromptTemplate.from_template("{input}"),
            HumanMessagePromptTemplate.from_template(
                "Учитывая приведенный выше разговор, составь поисковый запрос для получения релевантной информации."
            ),
        ])
        return create_history_aware_retriever(llm, retriever, prompt)
    except Exception as e:
        logger.error(f"Ошибка создания цепочки ретривера: {e}")
        raise


async def create_rag_chain(retriever_chain, llm, prompt_text):
    """Создание цепочки RAG"""
    try:
        logger.info("Создание RAG цепочки.")

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(f"{prompt_text}\nДокумент с информацией:\n\n{{context}}"),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
        stuff_chain = create_stuff_documents_chain(llm, prompt)
        return create_retrieval_chain(retriever_chain, stuff_chain)
    except Exception as e:
        logger.error(f"Ошибка создания RAG цепочки: {e}")
        raise


async def response_answer(user_id, text, language, history, prompt, bot):
    """Обработка запроса пользователя"""
    try:
        formatted_history = []

        for entry in history:
            if 'question' in entry:
                formatted_history.append({"role": "user", "content": entry['question']})
            if 'response' in entry:
                formatted_history.append({"role": "assistant", "content": entry['response']})

        llm = ChatOpenAI(model_name=MODEL_GPT4, openai_api_key=API_KEY)
        logger.info(f"Модель OpenAI: {MODEL_GPT4}")

        total_tokens_input = count_total_tokens(history, text, model=MODEL_GPT4)
        logger.info(f"Токены запроса: {total_tokens_input}")

        limit = get_user_limit(user_id)
        if limit - total_tokens_input <= 0:
            logger.warning("Недостаточно токенов.")
            await bot.edit_message_text(chat_id=user_id, text=MESSAGES["token_limit_exceeded"]["ru"])
            return

        retriever_chain = await create_retriever_chain(llm, prompt)
        if not retriever_chain:
            raise ValueError("retriever_chain не создан")

        rag_chain = await create_rag_chain(retriever_chain, llm, prompt)
        if not rag_chain:
            raise ValueError("rag_chain не создан")

        response = await asyncio.to_thread(rag_chain.invoke, {
            "history": formatted_history,
            "input": text
        })

        if response is None or "answer" not in response:
            logger.error(f"Некорректный ответ от RAG цепочки: {response}")
            raise ValueError("Некорректный ответ от RAG цепочки")

        response_text = response['answer']
        total_tokens_response = count_tokens(response_text, model=MODEL_GPT4)

        update_user_limit(user_id, limit - (total_tokens_input + total_tokens_response))

        return response_text
    except OpenAIError as e:
        logger.error(f"OpenAI Error: {e}", exc_info=True)
        await bot.edit_message_text(chat_id=user_id, text=MESSAGES["processing_error"]["en"])
        return
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}", exc_info=True)
        await bot.edit_message_text(chat_id=user_id, text=MESSAGES["unexpected_error"]["en"])
        return
