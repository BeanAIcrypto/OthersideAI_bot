from typing import Any
from langchain.tools import BaseTool
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import logging
import requests


logger = logging.getLogger(__name__)

class GoogleSearchAPIWrapper(BaseTool):
    name: str = "Google Search"
    description: str = "Инструмент для выполнения поиска в Google с загрузкой содержимого страниц."
    api_key: str
    search_engine_id: str
    service: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def _fetch_page_content(self, url: str) -> str:
        """Загрузка и парсинг содержимого страницы."""
        try:
            logger.info(f"Загрузка содержимого страницы: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator='\n')
            return text[:90000]
        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы {url}: {e}")
            return "Не удалось загрузить содержимое страницы."

    def _run(self, query: str) -> str:
        """Синхронная реализация поиска в Google."""
        try:
            logger.info(f"Выполняем поиск в Google по запросу: '{query}'")
            res = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=3).execute()
            if 'items' not in res:
                return "Результаты поиска не найдены."
            results = res['items']

            detailed_results = []
            for item in results:
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                page_content = self._fetch_page_content(link)
                detailed_results.append(
                    f"Заголовок: {title}\nОтрывок: {snippet}\nСсылка: {link}\nСодержимое:\n{page_content}")

            return "\n\n".join(detailed_results)

        except Exception as e:
            logger.error(f"Ошибка при выполнении Google Search: {e}")
            return "Ошибка при выполнении поиска."

    async def _arun(self, query: str) -> str:
        """Асинхронная версия не реализована."""
        raise NotImplementedError("Асинхронная функция _arun не реализована.")
