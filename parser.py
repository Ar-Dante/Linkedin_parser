import json
import logging
import os
from typing import Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from models import ProfileData, CompanyData, JobData
from config import SELECTORS, DATA_FOLDER, PROFILES_FILE, COMPANIES_FILE, JOBS_FILE, SEARCH_RESULTS_FILE

logger = logging.getLogger(__name__)


class LinkedInParser:
    """Parser for LinkedIn data extraction"""

    @staticmethod
    def parse_profile_from_search(element: WebElement, keywords: str, location: Optional[str] = None) -> Optional[
        ProfileData]:
        """Parse profile data from search result element"""
        try:
            try:
                profile_link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
            except:
                profile_link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/search/results/people/headless"]')

            profile_url = profile_link_elem.get_attribute('href')
            if not profile_url or profile_url == "#":
                return None

            if '?' in profile_url:
                profile_url = profile_url.split('?')[0]

            name = "LinkedIn Member"
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, 'span[dir="ltr"] span[aria-hidden="true"]')
                name = name_elem.text.strip()
            except:
                try:
                    link_with_name = element.find_element(By.CSS_SELECTOR,
                                                          'div.t-sans a[href*="/in/"], div.t-sans a[href*="/search/results/people/headless"]')
                    name_text = link_with_name.text.strip()
                    if name_text and name_text != "LinkedIn Member":
                        name = name_text
                except:
                    pass

            headline = ""
            try:
                headline_elem = element.find_element(By.CSS_SELECTOR, 'div.t-14.t-black.t-normal')
                headline = headline_elem.text.strip()
            except:
                pass

            location_text = ""
            try:
                location_elems = element.find_elements(By.CSS_SELECTOR, 'div.t-14.t-normal')
                if location_elems:
                    location_text = location_elems[-1].text.strip()
            except:
                pass

            return ProfileData(
                profile_url=profile_url,
                name=name,
                headline=headline,
                location=location_text,
                search_keywords=keywords,
                search_location=location
            )

        except Exception as e:
            logger.debug(f"Error parsing profile from search: {e}")
            return None

    @staticmethod
    def parse_company_from_search(element: WebElement, keywords: str, location: Optional[str] = None) -> Optional[
        CompanyData]:
        """Parse company data from search result element"""
        try:
            urn_attr = element.get_attribute('data-chameleon-result-urn')
            if not urn_attr:
                urn_element = element.find_element(By.CSS_SELECTOR, '[data-chameleon-result-urn]')
                urn_attr = urn_element.get_attribute('data-chameleon-result-urn') if urn_element else ""

            company_id = urn_attr.split(':')[-1] if urn_attr else ""

            company_link_elem = LinkedInParser._find_element_by_selectors(element, SELECTORS['company_link'])
            if not company_link_elem:
                return None

            company_url = company_link_elem.get_attribute('href')
            if not company_url or company_url == "#":
                return None

            if '?' in company_url:
                company_url = company_url.split('?')[0]

            name = LinkedInParser._extract_text(element, SELECTORS['company_name'], "Unknown Company")
            if not name and company_link_elem:
                name = company_link_elem.text.strip()

            industry_elem = LinkedInParser._find_element_by_selectors(element, SELECTORS['company_industry'])
            if industry_elem:
                industry_location_text = industry_elem.text.strip()
                if "•" in industry_location_text:
                    parts = industry_location_text.split("•")
                    industry = parts[0].strip()
                    location_text = parts[1].strip() if len(parts) > 1 else ""
                else:
                    industry = industry_location_text
                    location_text = ""
            else:
                industry = ""
                location_text = ""

            company_size = LinkedInParser._extract_text(element, SELECTORS['company_size'])
            summary = LinkedInParser._extract_text(element, SELECTORS.get('company_summary', []))

            return CompanyData(
                company_url=company_url,
                company_id=company_id,
                name=name,
                industry=industry,
                location=location_text,
                company_size=company_size,
                summary=summary,
                search_keywords=keywords,
                search_location=location
            )

        except Exception as e:
            logger.debug(f"Error parsing company from search: {e}")
            return None

    @staticmethod
    def parse_job_from_search(card: WebElement, keywords: str, location: Optional[str] = None) -> Optional[JobData]:
        """Parse job data from search result card"""
        try:
            job_id = card.get_attribute('data-occludable-job-id')

            job_link_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_link'])
            job_url = job_link_elem.get_attribute('href')

            try:
                job_title_elem = job_link_elem.find_element(By.CSS_SELECTOR, SELECTORS['job_title'])
                job_title = job_title_elem.text.strip()
            except:
                job_title = job_link_elem.get_attribute('aria-label').replace(' with verification', '').strip()

            if not job_id and '/view/' in job_url:
                job_id = job_url.split('/view/')[1].split('/')[0].split('?')[0]
            elif not job_id:
                job_id = job_url.split('/')[-1].split('?')[0]

            company_name = LinkedInParser._extract_text(card, SELECTORS['job_company'])
            job_location = LinkedInParser._extract_text(card, SELECTORS['job_location'])

            try:
                promoted_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_promoted'])
                is_promoted = "Promoted" in promoted_elem.text
            except:
                is_promoted = False

            try:
                time_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_time'])
                posted_time = time_elem.text.strip()
                posted_datetime = time_elem.get_attribute('datetime')
            except:
                posted_time = ""
                posted_datetime = ""

            try:
                card.find_element(By.CSS_SELECTOR, SELECTORS['job_easy_apply'])
                easy_apply = True
            except:
                easy_apply = False

            return JobData(
                job_id=job_id,
                job_url=job_url,
                title=job_title,
                company=company_name,
                location=job_location,
                posted_time=posted_time,
                posted_datetime=posted_datetime,
                is_promoted=is_promoted,
                easy_apply=easy_apply,
                search_keywords=keywords,
                search_location=location
            )

        except Exception as e:
            logger.debug(f"Error parsing job from search: {e}")
            return None

    def save_to_json(self, data: Union[
        ProfileData, CompanyData, JobData,
        list[ProfileData], list[CompanyData], list[JobData]
    ]):
        os.makedirs(DATA_FOLDER, exist_ok=True)

        items = data if isinstance(data, list) else [data]
        data_type = type(items[0]) if items else None

        file_map = {
            ProfileData: PROFILES_FILE,
            CompanyData: COMPANIES_FILE,
            JobData: JOBS_FILE
        }
        file_name = file_map.get(data_type, SEARCH_RESULTS_FILE)
        file_path = os.path.join(DATA_FOLDER, file_name)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.extend(item.__dict__ for item in items)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _find_element_by_selectors(parent: WebElement, selectors: list[str]) -> Optional[WebElement]:
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
    def _extract_text(parent: WebElement, selectors: list[str], default: str = "") -> str:
        """Helper method to extract text from element"""
        element = LinkedInParser._find_element_by_selectors(parent, selectors)
        return element.text.strip() if element else default
