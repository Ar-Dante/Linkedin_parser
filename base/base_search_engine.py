import logging
from abc import ABC, abstractmethod
from typing import Any

from undetected_chromedriver import WebElement

from linkedin_automation import LinkedInAutomation
from parser import LinkedInParser
from search_engine import EntityType, DataFile


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseSearchEngine(ABC):
    """Abstract base class for search engines"""

    def __init__(self, automation: LinkedInAutomation):
        self.automation = automation
        self.driver = automation.driver
        self.parser = LinkedInParser()

    @abstractmethod
    async def search_entities(self, entity_type: EntityType, keywords: str,
                              location: str | None = None, max_results: int = 50) -> list[Any]:
        """Abstract method for searching entities"""
        pass

    @abstractmethod
    async def get_search_results(self, selector_key: str) -> list[WebElement]:
        """Abstract method for getting search results"""
        pass

    async def save_results(self, results: list[Any], data_file: DataFile) -> None:
        """Save search results to file"""
        await self.automation.save_entities(results, data_file.full_path)
        logger.info(f"Saved {len(results)} results to {data_file.full_path}")