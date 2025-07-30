from abc import ABC
from typing import Union, Optional

from selenium.webdriver.common.by import By
from undetected_chromedriver import WebElement


class BaseParser(ABC):
    """Abstract base class for LinkedIn data parsing"""

    @staticmethod
    def _find_element_by_selectors(parent: WebElement, selectors: Union[str, list[str]]) -> Optional[WebElement]:
        """Helper method to find element using multiple selectors"""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                element = parent.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        return None

    @staticmethod
    def _extract_text(parent: WebElement, selectors: Union[str, list[str]], default: str = "") -> str:
        """Helper method to extract text from element"""
        element = BaseParser._find_element_by_selectors(parent, selectors)
        return element.text.strip() if element else default

    @staticmethod
    def _clean_url(url: str) -> Optional[str]:
        """Clean URL by removing query parameters"""
        if not url or url == "#":
            return None
        return url.split('?')[0]
