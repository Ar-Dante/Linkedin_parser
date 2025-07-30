import asyncio
import logging
import random
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from selenium.webdriver.common.by import By
from undetected_chromedriver import WebElement

from base.base_search_engine import BaseSearchEngine
from config import LINKEDIN_URL, SELECTORS, DATA_FOLDER
from models import CompanyData, ProfileData, JobData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Enum for LinkedIn search entity types"""
    PEOPLE = "people"
    COMPANIES = "companies"
    JOBS = "jobs"


class DataFile(Enum):
    """Enum for data file paths with descriptive names"""
    PROFILES = "profiles.json"
    COMPANIES = "companies.json"
    JOBS = "jobs.json"

    @property
    def full_path(self) -> str:
        """Get full file path"""
        return str(Path(DATA_FOLDER) / self.value)


class LinkedInSearchEngine(BaseSearchEngine):
    """LinkedIn-specific search engine implementation"""

    async def search_people(self, keywords: str, location: str | None = None, max_results: int = 50) -> list[
        ProfileData]:
        """Search for people on LinkedIn"""
        logger.info(f"Starting people search: keywords='{keywords}', location='{location}', max_results={max_results}")

        results = await self.search_entities(
            entity_type=EntityType.PEOPLE,
            keywords=keywords,
            location=location,
            max_results=max_results,
        )

        await self.save_results(results, DataFile.PROFILES)
        logger.info(f"Completed people search: found {len(results)} profiles")
        return results

    async def search_companies(self, keywords: str, location: str | None = None, max_results: int = 50) -> list[
        CompanyData]:
        """Search for companies on LinkedIn"""
        logger.info(f"Starting company search: keywords='{keywords}', location='{location}', max_results={max_results}")

        results = await self.search_entities(
            entity_type=EntityType.COMPANIES,
            keywords=keywords,
            location=location,
            max_results=max_results,
        )

        await self.save_results(results, DataFile.COMPANIES)
        logger.info(f"Completed company search: found {len(results)} companies")
        return results

    async def search_jobs(self, keywords: str, location: str | None = None, max_results: int = 50) -> list[JobData]:
        """Search for jobs on LinkedIn"""
        if not self.automation.logged_in:
            logger.error("Cannot search jobs: not logged in!")
            return []

        logger.info(f"Starting job search: keywords='{keywords}', location='{location}', max_results={max_results}")

        try:
            search_url = f"{LINKEDIN_URL}/jobs/search/?keywords={quote(keywords)}"
            if location:
                search_url += f"&location={quote(location)}"

            logger.debug(f"Navigating to job search URL: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            results = []
            processed_ids = set()
            page = 1

            while len(results) < max_results:
                logger.info(f"Processing job search page {page}... (found {len(results)}/{max_results} jobs so far)")

                job_cards = await self._get_job_cards()
                if not job_cards:
                    logger.warning(f"No job cards found on page {page}")
                    break

                logger.debug(f"Found {len(job_cards)} job cards on page {page}")

                for i, card in enumerate(job_cards, 1):
                    if len(results) >= max_results:
                        break

                    job_data = self.parser.parse_job_from_search(card, keywords, location)
                    if job_data and job_data.job_id not in processed_ids:
                        processed_ids.add(job_data.job_id)
                        results.append(job_data)
                        logger.debug(f"Page {page}, Card {i}: Found job '{job_data.title}' at '{job_data.company}'")

                logger.info(f"Page {page} processed: {len(results)} total jobs found")

                if not await self._load_more_jobs(len(job_cards)):
                    logger.info(f"No more job pages available after page {page}")
                    break

                page += 1

            await self.save_results(results, DataFile.JOBS)
            logger.info(f"Completed job search: found {len(results)} jobs across {page} pages")
            return results

        except Exception as e:
            logger.error(f"Error during job search: {e}")
            return []

    async def search_entities(self, entity_type: EntityType, keywords: str,
                              location: str | None = None, max_results: int = 50) -> list[Any]:
        """Generic search method for different entity types"""
        if not self.automation.logged_in:
            logger.error(f"Cannot search {entity_type.value}: not logged in!")
            return []

        try:
            logger.info(
                f"Starting {entity_type.value} search: keywords='{keywords}', location='{location}', max_results={max_results}")

            search_url = f"{LINKEDIN_URL}/search/results/{entity_type.value}/?keywords={quote(keywords)}"
            if location:
                search_url += f"&geoUrn={location}"

            logger.debug(f"Navigating to search URL: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            results = []
            page = 1
            parser_method = self._get_parser_method(entity_type)
            while len(results) < max_results:
                logger.info(
                    f"Processing {entity_type.value} search page {page}... (found {len(results)}/{max_results} results so far)")

                elements = await self.get_search_results('search_results')

                if not elements:
                    logger.warning(f"No elements found on page {page}, trying scroll and retry...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(2)
                    elements = await self.get_search_results('search_results')

                    if not elements:
                        logger.warning(f"Still no elements found on page {page}, ending search")
                        break

                logger.debug(f"Found {len(elements)} elements to parse on page {page}")

                parsed_count = 0
                for i, element in enumerate(elements, 1):
                    if len(results) >= max_results:
                        break

                    parsed_data = parser_method(element, keywords, location)
                    if parsed_data:
                        results.append(parsed_data)
                        parsed_count += 1
                        logger.debug(
                            f"Page {page}, Element {i}: Successfully parsed {entity_type.value} result #{len(results)}")

                logger.info(
                    f"Page {page} processed: {parsed_count}/{len(elements)} elements parsed successfully, {len(results)} total results")

                if not await self._go_to_next_page():
                    logger.info(f"No more pages available after page {page}")
                    break

                page += 1

            logger.info(f"Completed {entity_type.value} search: found {len(results)} results across {page} pages")
            return results

        except Exception as e:
            logger.error(f"Error searching {entity_type.value}: {e}")
            return []

    async def get_search_results(self, selector_key: str) -> list[WebElement]:
        """Get search result elements with multiple selector strategies"""
        try:
            await asyncio.sleep(2)
            selectors = SELECTORS.get(selector_key, SELECTORS['search_results'])
            if isinstance(selectors, str):
                selectors = [selectors]

            for i, selector in enumerate(selectors, 1):
                try:
                    logger.debug(f"Trying selector {i}/{len(selectors)}: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    valid_elements = []
                    for element in elements:
                        valid_elements.append(element)

                    if valid_elements:
                        logger.debug(f"Found {len(valid_elements)} search results with selector {i}: {selector}")
                        return valid_elements

                except Exception as e:
                    logger.debug(f"Selector {i} failed: {e}")
                    continue

            logger.warning("No search results found with any selector")
            return []

        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []

    def _get_parser_method(self, entity_type: EntityType) -> Callable:
        """Get the appropriate parser method for entity type"""
        parser_map = {
            EntityType.PEOPLE: self.parser.parse_profile_from_search,
            EntityType.COMPANIES: self.parser.parse_company_from_search,
            EntityType.JOBS: self.parser.parse_job_from_search,
        }
        return parser_map[entity_type]

    async def _get_job_cards(self) -> list[WebElement]:
        """Get job card elements"""
        logger.debug("Looking for job cards...")
        for i, selector in enumerate(SELECTORS['job_cards'], 1):
            try:
                logger.debug(f"Trying job card selector {i}/{len(SELECTORS['job_cards'])}: {selector}")
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.debug(f"Found {len(cards)} job cards with selector {i}")
                    return cards
            except Exception as e:
                logger.debug(f"Job card selector {i} failed: {e}")
                continue

        logger.warning("No job cards found with any selector")
        return []

    async def _load_more_jobs(self, current_count: int) -> bool:
        """Load more job results"""
        try:
            logger.debug("Attempting to load more jobs...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(random.uniform(2, 3))

            new_cards = await self._get_job_cards()
            if len(new_cards) == current_count:
                logger.debug("Card count unchanged, looking for 'See more' button...")
                try:
                    see_more_btn = self.driver.find_element(By.XPATH, SELECTORS['see_more_button'])
                    self.driver.execute_script("arguments[0].click();", see_more_btn)
                    await asyncio.sleep(random.uniform(2, 3))
                    logger.debug("Clicked 'See more' button")
                    return True
                except Exception as e:
                    logger.debug(f"'See more' button not found: {e}, trying next page...")
                    return await self._go_to_next_page()

            logger.debug(f"New cards loaded: {len(new_cards)} (was {current_count})")
            return True

        except Exception as e:
            logger.debug(f"Error loading more jobs: {e}")
            return False

    async def _go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        logger.debug("Attempting to navigate to next page...")
        for i, selector in enumerate(SELECTORS['next_page_button'], 1):
            try:
                logger.debug(f"Trying next page selector {i}/{len(SELECTORS['next_page_button'])}: {selector}")
                next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if next_button.is_enabled() and not next_button.get_attribute('disabled'):
                    await self.automation._safe_click(next_button)
                    await asyncio.sleep(random.uniform(3, 5))
                    logger.debug(f"Successfully clicked next page button with selector {i}")
                    return True
                else:
                    logger.debug(f"Next page button found but disabled with selector {i}")
            except Exception as e:
                logger.debug(f"Next page selector {i} failed: {e}")
                continue

        logger.debug("No working next page button found")
        return False
