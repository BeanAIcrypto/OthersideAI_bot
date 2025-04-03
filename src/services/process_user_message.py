import re
from src.services.gpt_response_handler_text import response_answer
from src.keyboards.drating_inline_buttons_keyboard import drating_inline_buttons_keyboard
from aiogram.types import ChatActions
import logging
from db.dbworker import (get_user_limit,
                         update_user_limit,
                         add_history_entry)

from src.bot.bot_messages import MESSAGES, MESSAGES_ERROR
from dotenv import load_dotenv
from src.converter.image_processing import image_processing
from src.bot.promt import PROMTS

load_dotenv()

logger = logging.getLogger(__name__)


def latex_to_unicode(text: str) -> str:
    """
    Преобразует LaTeX выражения в Unicode.

    Args:
        text (str): Текст, содержащий LaTeX выражения.

    Returns:
        str: Текст, преобразованный в Unicode.

    Raises:
        Exception: Логирует ошибку, если что-то пошло не так при преобразовании.
    """
    try:
        text = re.sub(
            r"\\\[(.*?)\\\]",
            lambda m: m.group(1).strip(),
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"\\\((.*?)\\\)",
            lambda m: m.group(1).strip(),
            text,
            flags=re.DOTALL,
        )
        text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
        text = re.sub(
            r"\\frac\{([^}]*)\}\{([^}]*)\}",
            lambda m: f"({m.group(1)})/({m.group(2)})",
            text,
        )

        greek_map = {
            r"\alpha": "α",
            r"\beta": "β",
            r"\gamma": "γ",
            r"\delta": "δ",
            r"\epsilon": "ε",
            r"\zeta": "ζ",
            r"\eta": "η",
            r"\theta": "θ",
            r"\iota": "ι",
            r"\kappa": "κ",
            r"\lambda": "λ",
            r"\mu": "μ",
            r"\nu": "ν",
            r"\xi": "ξ",
            r"\omicron": "ο",
            r"\pi": "π",
            r"\rho": "ρ",
            r"\sigma": "σ",
            r"\tau": "τ",
            r"\upsilon": "υ",
            r"\phi": "φ",
            r"\chi": "χ",
            r"\psi": "ψ",
            r"\omega": "ω",
            r"\Gamma": "Γ",
            r"\Delta": "Δ",
            r"\Theta": "Θ",
            r"\Lambda": "Λ",
            r"\Xi": "Ξ",
            r"\Pi": "Π",
            r"\Sigma": "Σ",
            r"\Upsilon": "Υ",
            r"\Phi": "Φ",
            r"\Psi": "Ψ",
            r"\Omega": "Ω",
        }
        for latex_cmd, uni_char in greek_map.items():
            text = text.replace(latex_cmd, uni_char)

        math_symbols = {
            r"\times": "×",
            r"\cdot": "⋅",
            r"\approx": "≈",
            r"\leq": "≤",
            r"\geq": "≥",
            r"\neq": "≠",
            r"\pm": "±",
            r"\mp": "∓",
            r"\to": "→",
            r"\leftarrow": "←",
            r"\Rightarrow": "⇒",
            r"\Leftarrow": "⇐",
            r"\leftrightarrow": "↔",
            r"\infty": "∞",
            r"\partial": "∂",
            r"\aleph": "ℵ",
            r"\hbar": "ℏ",
            r"\%": "%",
        }
        for latex_cmd, uni_char in math_symbols.items():
            text = text.replace(latex_cmd, uni_char)

        math_functions = {
            r"\sqrt": "√",
            r"\sum": "∑",
            r"\int": "∫",
            r"\prod": "∏",
            r"\lim": "lim",
            r"\ln": "ln",
            r"\sin": "sin",
            r"\cos": "cos",
            r"\tan": "tan",
            r"\log": "log",
            r"\exp": "exp",
        }
        for func, uni_char in math_functions.items():
            if func == r"\sqrt":
                text = re.sub(
                    r"\\sqrt\{([^}]*)\}", lambda m: "√" + m.group(1), text
                )
            else:
                text = text.replace(func, uni_char)

        superscript_map = {
            "0": "⁰",
            "1": "¹",
            "2": "²",
            "3": "³",
            "4": "⁴",
            "5": "⁵",
            "6": "⁶",
            "7": "⁷",
            "8": "⁸",
            "9": "⁹",
            "+": "⁺",
            "-": "⁻",
            "=": "⁼",
            "(": "⁽",
            ")": "⁾",
            "n": "ⁿ",
            "i": "ⁱ",
            "t": "ᵗ",
            "m": "ᵐ",
            "r": "ʳ",
            "s": "ˢ",
            "u": "ᵘ",
            "v": "ᵛ",
            "j": "ʲ",
            "d": "ᵈ",
            "g": "ᵍ",
            "a": "ᵃ",
            "b": "ᵇ",
            "c": "ᶜ",
            "f": "ᶠ",
            "k": "ᵏ",
            "l": "ˡ",
            "o": "ᵒ",
            "p": "ᵖ",
            "q": "ᑫ",
            "w": "ʷ",
            "x": "ˣ",
            "y": "ʸ",
            "z": "ᶻ",
        }

        def replace_superscript(match: re.Match) -> str:
            content = match.group(1)
            return "".join(superscript_map.get(ch, ch) for ch in content)

        text = re.sub(r"\^\{([^}]*)\}", replace_superscript, text)

        text = re.sub(
            r"\^(\w)",
            lambda m: superscript_map.get(m.group(1), m.group(1)),
            text,
        )

        subscript_map = {
            "0": "₀",
            "1": "₁",
            "2": "₂",
            "3": "₃",
            "4": "₄",
            "5": "₅",
            "6": "₆",
            "7": "₇",
            "8": "₈",
            "9": "₉",
            "+": "₊",
            "-": "₋",
            "=": "₌",
            "(": "₍",
            ")": "₎",
            "a": "ₐ",
            "e": "ₑ",
            "o": "ₒ",
            "x": "ₓ",
            "h": "ₕ",
            "k": "ₖ",
            "l": "ₗ",
            "m": "ₘ",
            "n": "ₙ",
            "p": "ₚ",
            "s": "ₛ",
            "t": "ₜ",
            "u": "ᵤ",
            "v": "ᵥ",
            "i": "ᵢ",
            "r": "ᵣ",
            "d": "ᵈ",
            "g": "ᵍ",
            "j": "ʲ",
            "c": "ₓ",
            "f": "ₓ",
            "b": "ₓ",
        }

        def replace_subscript(match: re.Match) -> str:
            content = match.group(1)
            return "".join(subscript_map.get(ch, ch) for ch in content)

        text = re.sub(r"\\?_\{([^}]*)\}", replace_subscript, text)

        text = re.sub(
            r"\\?_(\w)",
            lambda m: subscript_map.get(m.group(1), m.group(1)),
            text,
        )

    except Exception as e:
        logger.error(f"Ошибка преобразования LaTeX в Unicode: {str(e)}")

    return text


def convert_markdown_to_markdownv2(text: str) -> str:
    """
    Преобразует текст Markdown в формат MarkdownV2 для Telegram,
    обрабатывая блоки кода, специальные символы и LaTeX-выражения.

    Args:
        text (str): Текст в формате Markdown.

    Returns:
        str: Текст, преобразованный в формат MarkdownV2.
    """
    try:
        special_chars = r"\[\]()~`>#+\-=|{}.!"

        link_pattern = re.compile(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)")
        links = {}

        def save_link(match):
            text, url = match.groups()
            text = re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)
            placeholder = f"%%LINK{len(links)}%%"
            links[placeholder] = f"[{text}]({url})"
            return placeholder

        text = link_pattern.sub(save_link, text)
        text = latex_to_unicode(text)

        def escape_special_chars(part: str) -> str:
            """Экранирует спецсимволы MarkdownV2, но не трогает _ внутри юзернеймов."""
            part = re.sub(r"([{}])".format(re.escape(special_chars)), r"\\\1", part)
            return part

        def process_text_part(part: str) -> str:
            """Обрабатывает обычный текст, не затрагивая кодовые блоки."""
            part = re.sub(r"(?<!\\)_", r"\_", part)
            part = re.sub(r"\*\*(.*?)\*\*", r"*\1*", part)
            part = re.sub(r"##### (.*?)\n", r"__\1__\n", part)
            part = re.sub(r"#### (.*?)\n", r"__\1__\n", part)
            part = re.sub(r"### (.*?)\n", r"__\1__\n", part)
            part = re.sub(r"## (.*?)\n", r"__\1__\n", part)
            part = re.sub(r"# (.*?)\n", r"__\1__\n", part)
            part = re.sub(r"__(.*?)__", r"__\1__", part)

            return escape_special_chars(part)

        code_block_pattern = re.compile(r"(```.*?```)", re.DOTALL)
        parts = code_block_pattern.split(text)

        processed_parts = [
            part if part.startswith("```") else process_text_part(part)
            for part in parts
        ]

        result = "".join(processed_parts)

        for placeholder, link in links.items():
            result = result.replace(placeholder, link)

        return result

    except Exception as e:
        logger.error(f"Ошибка перевода в MarkdownV2: {str(e)}")
        return text


async def process_user_message(user_id, user_name, text, language, history, prompt, bot, message = None, chat_id=None, file_url=None):
    try:
        logger.info(f"Вызов модели для пользователя {user_name} (ID: {user_id}) с запросом: {text[:500]}")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
        await bot.send_chat_action(chat_id=user_id, action='typing')

        first_message = await bot.send_message(chat_id=user_id, text=MESSAGES["process_user_message"][language])
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
        if prompt == 'image' :
            response = await image_processing(message, text, bot, user_id, file_url, prompt=PROMTS[prompt][language])
        else:
            response = await response_answer(user_id, text, language, history, prompt, bot)

        if not response:
            raise ValueError("Empty response received")

        await bot.send_chat_action(chat_id=user_id, action='typing')
        logger.info(f"Сообщения от модели: {response}")
        assistant_response_id = add_history_entry(user_id, text, response)

        if chat_id == user_id:
            rating_keyboard = drating_inline_buttons_keyboard(assistant_response_id)
            rating_message = MESSAGES["rating_request"].get(language)
        else:
            rating_keyboard = None
            rating_message = ''

        response_with_rating = response + '\n' + rating_message

        try:
            formatted_text = convert_markdown_to_markdownv2(response_with_rating)
        except Exception as e:
            logger.error(f"Ошибка перевода текста в MarkdownV2: {e}")
            await bot.send_message(chat_id=user_id, text=MESSAGES_ERROR["markdown_error"][language])
            return
        logger.info(f"Сообщения от модели в формате markdownv2: {formatted_text}")

        await bot.send_message(
            chat_id=user_id,
            text=formatted_text,
            reply_markup=rating_keyboard,
            parse_mode="MarkdownV2"
        )

        await bot.delete_message(chat_id=user_id, message_id=first_message.message_id)

        logger.info(f"Обработка сообщения от пользователя {user_name} завершена")
    except ValueError as ve:
        logger.error(f"Ошибка: {ve}", exc_info=True)
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=first_message.message_id,
            text=MESSAGES_ERROR["error_response"][language]
        )
    except Exception as e:
        logger.error(f"Произошла ошибка обработки сообщения: {e}",exc_info=True)
        await bot.send_message(chat_id=user_id, text=MESSAGES_ERROR["error_response"][language])

