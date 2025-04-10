# OthersideAI_bot

## 📌 Project Description
**OthersideAI_bot** is a smart Telegram bot that promptly and accurately answers any questions about the Otherside meta-universe, NFT, cryptocurrencies and financial strategies.

Using the advanced GPT-4o model, the bot analyzes data in real time, saving you time and providing the most up-to-date information.

---

## 🔍 What OthersideAI_bot can do

**Your all-in-one assistant in the meta universe and beyond**.

1. 💬 **OthersideAI_bot **One-click Q&A**

Get instant answers to any questions you have about the **Otherside** meta universe, NFT, virtual real estate, and the crypto industry.   

2. 📄 Smart **Site and Document Analysis**  
  
Upload an article or PDF - the bot will quickly highlight key ideas and generate an understandable short paraphrase.

3. 🎥 Quick **parsing of YouTube videos**  
   
Upload a link to a YouTube video and get a concise summary with key ideas and recommendations without having to watch it.

4. 🖼 **Image Recognition**  
   
Submit an image - the bot will analyze it and provide a helpful comment or explanation.

---

## ⚙️ **How to interact with OthersideAI_bot**

- Via **Telegram chats**

Add the bot to a private or group chat; it activates when you mention it directly.

- **Support for any query**

From simple questions to in-depth analytics, ask freely.

- **Work with files and links**

Just send the bot a document, link to an article or video - the bot will do everything for you.

---

## 🚀 Why is it convenient?

**Maximum benefit - minimum effort**.

- **Instant answers**

No need to waste time searching - get the information you need right away.

- **Up-to-date information**

Constant updates and trend monitoring.

- **All in one place**

Analyze text, video, images and links in a single tool.

- **Group Chat Support**

Easy integration into any discussion.  

---

## 📈 Improved response quality

**OthersideAI_bot** is constantly improving thanks to:

- **Feedback from users**

Every suggestion, comment or idea you have helps make the bot better.

- **Expert verification**.

Content is verified by community members to ensure accuracy and validity.

- **Automated response evaluation**

The bot analyzes its own responses and adjusts approaches based on internal quality metrics.

- **Tracking relevant topics**

Regular monitoring of popular queries on the Otherside meta-universe allows you to quickly replenish your knowledge base.  

---

## 🛠️ Technologies and libraries

**OthersideAI_bot** is built on a modern technology stack providing stable operation, high performance and flexibility.

### Core technologies
- **Python 3.x** - the language on which the bot logic is built.
- **Telegram Bot API (aiogram 2.25.1)** - library for asynchronous work with Telegram.
- **OpenAI GPT-4o API (openai 1.57.2)** - language model responsible for generating responses.

### Data processing and analysis
- **LangChain 0.3.11**, **LangChain Community 0.3.11**, **LangChain OpenAI 0.2.10** - framework for working with LLMs
- **Tiktoken 0.7.0** - request tokenization
- **Pandas 2.2.3** - structured data analysis and transformation
- **FAISS-cpu 1.9.0.post1** - vector search on knowledge base

### Internet and data parsing
- **Playwright 1.47.0**
- **Cloudscraper 1.2.71**
- **Requests 2.32.3**
- **BeautifulSoup4 4.12.3**
- **aiohttp 3.8.6**
- **google-api-python-client 2.145.0**

### Document and media handling
- **python-docx 1.1.2**, **python-pptx 1.0.2**, **PyPDF2 3.0.1**
- **youtube-transcript-api 0.6.3**
- **ffmpeg**

### Databases and caching
- **psycopg2-binary 2.9.10**

---

## ⚙️ Project Configuration

Create an `.env` file and specify environment variables:

```
GPT_SECRET_KEY_FASOLKAAI=your_secret_key_OpenAI
MODEL_NAME=main_model_name
MODEL_NAME_MEM=memory_model_name

TG_TOKEN=token_telegram_bot
CHANNEL_ID=channel_id_Telegram
CHANNEL_LINK=link_to_Telegram_channel

SERVICE_ACCOUNT_FILE=path_to_file_of_Google_account_service_file
SPREADSHEET_ID=Google_table_id

GRASPIL_API_KEY=API_Graspil_key
TARGET_START_ID_LIMIT=start_limit_ID
TARGET_START_ID_START=start_ID_target_ID
TARGET_START_ID_BLOCK=lock_ID_target_ID

GOOGLE_API_KEY=API_Google_key
SEARCH_ENGINE_GLOBAL_ID=Google_search_engine_id

LANGCHAIN_TRACING_V2=True_or_False
LANGCHAIN_ENDPOINT= end_Langchain_point
LANGCHAIN_API_KEY=API_Langchain_key
LANGCHAIN_PROJECT=Langchain project_name

DB_HOST=database_host
DB_PORT=database_port
DB_NAME=data_base_name
DB_USER=data_base_user
DB_PASSWORD=data_base_user_password
```
---

## 🚀 Install and run the project locally

1. **Clone the repository**:
   ```bash
   git clone git@github.com:YourOrg/OthersideAI_bot.git
   ```
2. **Create and activate the virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate # Linux/MacOS
   venv\Scripts\activate # Windows.
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Customize environment variables**
5. **Start the project**:
   ```bash
   python app.py
   ```

---

## 🚀 Start a project using Docker

1. **Collect the Docker image**:
   ```bash
   docker build -t othersideai_bot .
   ```
2. **Build and start the container**:
   ````bash
   docker run -d othersideai_bot.
   ```

---


**OthersideAI_bot** is a modular, scalable system built in Python and integrated with modern AI and parsing tools.

1. **Backend logic**.
   - **Language**: Python 3
   - **Framework**: [aiogram] - asynchronous interaction with Telegram Bot API
   - **Response Generation**: OpenAI GPT-4o via official API

2. **Working with databases**.
   - **PostgreSQL** - main RDBMS
	- **psycopg2-binary** - connect and work with database

3. **Integration with external services**
   - **Google API** - for access to third-party content
   - **FAISS** - vector search on internal knowledge base

4. **Parsing and Automation**
   - **Playwright** - automate browser actions and render dynamic content
   - **BeautifulSoup4*** - HTML page processing and data extraction

---

## 👥 Authors

The project is developed and maintained by:
- **Berkina Diana** - [GitHub](https://github.com/DIprooger), [Telegram](https://t.me/di_berkina)
- **Founder and CEO of BeanAI** - GitHub (https://github.com/vladguru), [Telegram](https://t.me/vladguru_AI)

If you have any questions or ideas, contact the authors!

Translated with DeepL.com (free version)
