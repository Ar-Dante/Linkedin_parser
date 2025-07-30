import asyncio
import logging
import random
from typing import Optional
from urllib.parse import quote

from selenium.webdriver.common.by import By
from undetected_chromedriver import WebElement

from config import LINKEDIN_URL, SELECTORS, DATA_FOLDER, JOBS_FILE, PROFILES_FILE, COMPANIES_FILE
from linkedin_automation import LinkedInAutomation
from models import CompanyData, ProfileData, JobData
from parser import LinkedInParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(self, automation: LinkedInAutomation):
        self.automation = automation
        self.driver = automation.driver
        self.parser = LinkedInParser()

    async def search_people(self, keywords: str, location: Optional[str] = None, max_results: int = 50) -> list[
        ProfileData]:
        """Search for people on LinkedIn"""
        results = await self._search_entities(
            entity_type="people",
            keywords=keywords,
            location=location,
            max_results=max_results,
            parser_method=self.parser.parse_profile_from_search,
        )

        await self.automation.save_entities(results, f"{DATA_FOLDER}/{PROFILES_FILE}")
        return results

    async def search_companies(self, keywords: str, location: Optional[str] = None, max_results: int = 50) -> list[
        CompanyData]:
        """Search for companies on LinkedIn"""
        results = await self._search_entities(
            entity_type="companies",
            keywords=keywords,
            location=location,
            max_results=max_results,
            parser_method=self.parser.parse_company_from_search,
        )
        await self.automation.save_entities(results, f"{DATA_FOLDER}/{COMPANIES_FILE}")
        return results

    async def search_jobs(self, keywords: str, location: Optional[str] = None, max_results: int = 50) -> list[JobData]:
        """Search for jobs on LinkedIn"""
        if not self.automation.logged_in:
            logger.error("Not logged in!")
            return []

        try:
            logger.info(f"Searching for jobs: {keywords}, location: {location}")

            search_url = f"{LINKEDIN_URL}/jobs/search/?keywords={quote(keywords)}"
            if location:
                search_url += f"&location={quote(location)}"
            self.driver.get(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            results = []
            processed_ids = set()

            while len(results) < max_results:
                job_cards = await self._get_job_cards()

                for card in job_cards:
                    if len(results) >= max_results:
                        break
                    job_data = self.parser.parse_job_from_search(card, keywords, location)
                    if job_data and job_data.job_id not in processed_ids:
                        processed_ids.add(job_data.job_id)
                        results.append(job_data)
                        logger.info(f"Found job: {job_data.title} at {job_data.company}")

                if not await self._load_more_jobs(len(job_cards)):
                    break

            await self.automation.save_entities(results, f"{DATA_FOLDER}/{JOBS_FILE}")
            return results

        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []

    async def _search_entities(self, entity_type: str, keywords: str, location: Optional[str],
                               max_results: int, parser_method) -> list:
        """Generic search method for different entity types"""
        if not self.automation.logged_in:
            logger.error("Not logged in!")
            return []

        try:
            logger.info(f"Searching for {entity_type}: {keywords}, location: {location}")

            search_url = f"{LINKEDIN_URL}/search/results/{entity_type}/?keywords={quote(keywords)}"
            if location:
                search_url += f"&geoUrn={location}"

            self.driver.get(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            results = []
            page = 1

            while len(results) < max_results:
                logger.info(f"Processing page {page}...")
                elements = await self._get_search_results('search_results')
                print(elements)
                if not elements:
                    logger.warning(f"No elements found on page {page}")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(2)
                    elements = await self._get_search_results('search_results')
                    if not elements:
                        break

                logger.info(f"Found {len(elements)} elements to parse")

                for element in elements:
                    if len(results) >= max_results:
                        break

                    parsed_data = parser_method(element, keywords, location)
                    if parsed_data:
                        results.append(parsed_data)
                        logger.debug(f"Successfully parsed result #{len(results)}")

                logger.info(f"Parsed {len(results)} results so far")

                if not await self._go_to_next_page():
                    break

                page += 1

            return results

        except Exception as e:
            logger.error(f"Error searching {entity_type}: {e}")
            return []

    async def _get_search_results(self, selector_key: str) -> list[WebElement]:
        """Get search result elements with multiple selector strategies"""
        try:
            await asyncio.sleep(2)
            selectors = SELECTORS.get(selector_key, SELECTORS['search_results'])
            if isinstance(selectors, str):
                selectors = [selectors]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    valid_elements = []
                    for element in elements:
                        valid_elements.append(element)

                    if valid_elements:
                        logger.info(f"Found {len(valid_elements)} search results with selector: {selector}")
                        return valid_elements

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            logger.warning("No search results found with any selector")
            return []

        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []

    async def _get_job_cards(self) -> list:
        """Get job card elements"""
        for selector in SELECTORS['job_cards']:
            cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                return cards
        return []

    async def _load_more_jobs(self, current_count: int) -> bool:
        """Load more job results"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(random.uniform(2, 3))

            new_cards = await self._get_job_cards()
            if len(new_cards) == current_count:
                try:
                    see_more_btn = self.driver.find_element(By.XPATH, SELECTORS['see_more_button'])
                    self.driver.execute_script("arguments[0].click();", see_more_btn)
                    await asyncio.sleep(random.uniform(2, 3))
                    return True
                except:
                    return await self._go_to_next_page()

            return True

        except Exception as e:
            logger.debug(f"Error loading more jobs: {e}")
            return False

    async def _go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        for selector in SELECTORS['next_page_button']:
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if next_button.is_enabled() and not next_button.get_attribute('disabled'):
                    await self.automation._safe_click(next_button)
                    await asyncio.sleep(random.uniform(3, 5))
                    return True
            except:
                continue
        return False
