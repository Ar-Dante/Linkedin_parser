from abc import ABC, abstractmethod
import json
import logging
import os
from typing import Optional, Any, Union
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseAutomation(ABC):
    """Abstract base class for web automation"""

    def __init__(self):
        self.driver: Optional[WebDriver] = None
        self.logged_in: bool = False

    @abstractmethod
    async def setup_driver(self) -> None:
        """Initialize the web driver"""
        pass

    @abstractmethod
    async def login(self) -> bool:
        """Login to the platform"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the browser and cleanup"""
        pass

    @abstractmethod
    async def send_message(self, recipient_url: str, message: str) -> bool:
        """Send text message"""
        pass

    @abstractmethod
    async def send_voice_message(self, recipient_url: str, voice_file_path: str) -> bool:
        """Send voice message"""
        pass

    @abstractmethod
    async def check_response(self, recipient_url: str) -> Optional[bool]:
        """Check for responses"""
        pass

    @abstractmethod
    async def download_voice_messages(self, conversation_element) -> list[str]:
        """Download voice messages from conversation"""
        pass

    async def save_entities(self, entities: list[BaseModel], filepath: str) -> bool:
        """Generic method to save any pydantic model entities to JSON file"""
        try:
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            new_data = [entity.dict(exclude_none=True) for entity in entities]

            if isinstance(existing_data, list) and new_data:
                key_field = entities[0].get_key_field()
                existing_keys = {item.get(key_field) for item in existing_data if item.get(key_field)}

                unique_new_data = [
                    item for item in new_data
                    if item.get(key_field) not in existing_keys
                ]

                all_data = existing_data + unique_new_data
                logger.info(f"Added {len(unique_new_data)} new items to {filepath}")
            else:
                all_data = new_data

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(new_data)} items to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")
            return False

    def wait_for_element(self, selector: str, timeout: int = 10) -> Optional[Any]:
        """Wait for element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as e:
            logger.debug(f"Element not found: {selector}")
            return None

    def find_element_by_selectors(self, parent, selectors: Union[str, list[str]]) -> Optional[Any]:
        """Try multiple selectors to find an element"""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                element = parent.find_element(By.CSS_SELECTOR, selector)
                if element and (not hasattr(element, 'text') or element.text.strip()):
                    return element
            except:
                continue
        return None

    async def extract_text(self, parent, selectors: Union[str, list[str]], default: str = "") -> str:
        """Extract text from element using multiple selectors"""
        element = self.find_element_by_selectors(parent, selectors)
        return element.text.strip() if element else default
