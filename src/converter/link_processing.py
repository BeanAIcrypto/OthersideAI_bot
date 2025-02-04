import re
import logging
from src.bot.bot_messages import MESSAGES, MESSAGES_ERROR
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import aiohttp

logger = logging.getLogger(__name__)

def clean_text(text):
    try:
        text = re.sub(r"\* .+\n", '', text)
        text = re.sub(r"\+\d+ \(\d+\) \d+-\d+-\d+", "", text)
        text = re.sub(r"\w+@\w+\.\w+", "", text)
        text = re.sub(r"__+", "", text)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"©\s?\d{4}.+\n", "", text)
        text = re.sub(r"All rights reserved.?\n", "", text)
        text = re.sub(r"\n\s*\n", "\n", text)
        text = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4}", "", text)
        text = re.sub(r"\d{1,2}\.\d{1,2}\.\d{2,4}", "", text)

        text = re.sub(r"Follow us on .+\n", "", text)
        text = re.sub(r" {2,}", " ", text)
    except Exception as e:
        logger.error(f"Ошибка при очистке текста: {e}")
    return text

def html_to_text(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n')
    except Exception as e:
        logger.error(f"Ошибка преобразования HTML в текст: {e}")
        return ""

async def process_dynamic_page(url):
    try:
        logger.info(f"Начало обработки динамической страницы: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                response = await page.goto(url, wait_until='networkidle', timeout=60000)
            except TimeoutError:
                logger.error(MESSAGES_ERROR["dynamic_page_timeout"]["ru"])
                await browser.close()
                return None

            if response.status != 200:
                logger.error(f"Код ответа: {response.status}")
                await browser.close()
                return None

            content = await page.content()
            if "Please enable JavaScript" in content or "Checking your browser" in content:
                logger.error(MESSAGES_ERROR["dynamic_page_access_denied"]["ru"])
                await browser.close()
                return None

            text_content = html_to_text(content)
            cleaned_text = clean_text(text_content)

            logger.info(f"Очищенный текст: {cleaned_text[:200]}...")
            await browser.close()
            return cleaned_text

    except Exception as e:
        logger.error(MESSAGES_ERROR["dynamic_page_error"]["ru"])
        return None

async def process_static_page(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(MESSAGES_ERROR["static_page_error"]["ru"])
                    return None

                content = await response.text()

        text_content = html_to_text(content)
        cleaned_text = clean_text(text_content)

        logger.info(f"Очищенный текст: {cleaned_text[:200]}...")
        return cleaned_text

    except Exception as e:
        logger.error(MESSAGES_ERROR["static_page_error"]["ru"])
        return None

async def link_processing(url):
    try:
        logger.info(f"Начало обработки ссылки: {url}")

        static_content = await process_static_page(url)
        if static_content and len(static_content.strip()) > 500:
            logger.info(f"Ссылка обработана как статическая страница.")
            return static_content

        logger.info(f"Обработка как динамическая страница.")
        dynamic_content = await process_dynamic_page(url)
        return dynamic_content

    except Exception as e:
        logger.error(MESSAGES_ERROR["link_processing_error"]["ru"])
        return None

