import random
import time
import logging
import requests
from typing import Tuple
from fake_useragent import UserAgent
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def human_delay(min_sec: float = 1, max_sec: float = 3) -> None:
    """Simulate human-like delay between actions"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def human_typing(element, text: str, typing_delay: Tuple[float, float] = (0.1, 0.3)) -> None:
    """Type text with human-like speed"""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(*typing_delay))


def random_scroll(driver, scrolls: int = 3) -> None:
    """Perform random scrolling to simulate human behavior"""
    for _ in range(scrolls):
        scroll_height = random.randint(300, 700)
        direction = random.choice([1, -1])
        driver.execute_script(f"window.scrollBy(0, {scroll_height * direction})")
        human_delay(1, 2)


def move_to_element_human(driver, element) -> None:
    """Move to element with human-like mouse movement"""
    actions = ActionChains(driver)
    offset_x = random.randint(-5, 5)
    offset_y = random.randint(-5, 5)
    actions.move_to_element_with_offset(element, offset_x, offset_y).perform()
    human_delay(0.5, 1)


def check_proxy(proxy: str) -> bool:
    """Verify if proxy is working"""
    try:
        proxies = {'http': proxy, 'https': proxy}
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Proxy {proxy} check failed: {e}")
        return False


def get_random_user_agent() -> str:
    """Get random user agent"""
    ua = UserAgent()
    return ua.random


def wait_for_element(driver, selector: str, timeout: int = 10):
    """Wait for element to be present and return it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except Exception as e:
        logger.error(f"Element not found: {selector}, Error: {e}")
        return None


def safe_click(driver, element) -> bool:
    """Safely click an element with retry logic"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        human_delay(0.5, 1)

        element.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.error(f"Failed to click element: {e}")
            return False
