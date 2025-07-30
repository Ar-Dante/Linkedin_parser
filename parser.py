import json
import logging
import os
from abc import ABC
from typing import Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from base.base_parser import BaseParser
from models import ProfileData, CompanyData, JobData
from config import SELECTORS, DATA_FOLDER, PROFILES_FILE, COMPANIES_FILE, JOBS_FILE, SEARCH_RESULTS_FILE

logger = logging.getLogger(__name__)


class LinkedInParser(BaseParser):
    """Parser for LinkedIn data extraction"""

    def _parse_profile_name(self, element: WebElement) -> str:
        """Extract profile name"""
        try:
            name_elem = element.find_element(By.CSS_SELECTOR, 'span[dir="ltr"] span[aria-hidden="true"]')
            return name_elem.text.strip()
        except:
            try:
                link_elem = element.find_element(By.CSS_SELECTOR,
                                                 'div.t-sans a[href*="/in/"], div.t-sans a[href*="/search/results/people/headless"]')
                name_text = link_elem.text.strip()
                return name_text if name_text and name_text != "LinkedIn Member" else "LinkedIn Member"
            except:
                return "LinkedIn Member"

    def _parse_profile_url(self, element: WebElement) -> Optional[str]:
        """Extract profile URL"""
        try:
            profile_link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
        except:
            try:
                profile_link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/search/results/people/headless"]')
            except:
                return None

        url = profile_link_elem.get_attribute('href')
        return self._clean_url(url)

    def _parse_profile_location(self, element: WebElement) -> str:
        """Extract profile location"""
        try:
            location_elems = element.find_elements(By.CSS_SELECTOR, 'div.t-14.t-normal')
            return location_elems[-1].text.strip() if location_elems else ""
        except:
            return ""

    def _parse_company_id(self, element: WebElement) -> str:
        """Extract company ID from URN attribute"""
        urn_attr = element.get_attribute('data-chameleon-result-urn')
        if not urn_attr:
            try:
                urn_element = element.find_element(By.CSS_SELECTOR, '[data-chameleon-result-urn]')
                urn_attr = urn_element.get_attribute('data-chameleon-result-urn') if urn_element else ""
            except:
                urn_attr = ""
        return urn_attr.split(':')[-1] if urn_attr else ""

    def _parse_company_url(self, element: WebElement) -> Optional[str]:
        """Extract company URL"""
        company_link_elem = self._find_element_by_selectors(element, SELECTORS['company_link'])
        if not company_link_elem:
            return None
        url = company_link_elem.get_attribute('href')
        return self._clean_url(url)

    def _parse_company_name(self, element: WebElement, link_elem: WebElement) -> str:
        """Extract company name"""
        name = self._extract_text(element, SELECTORS['company_name'], "Unknown Company")
        if not name and link_elem:
            name = link_elem.text.strip()
        return name

    def _parse_industry_location(self, element: WebElement) -> tuple[str, str]:
        """Extract industry and location from combined text"""
        industry_elem = self._find_element_by_selectors(element, SELECTORS['company_industry'])
        if industry_elem:
            text = industry_elem.text.strip()
            if "•" in text:
                parts = text.split("•")
                industry = parts[0].strip()
                location_text = parts[1].strip() if len(parts) > 1 else ""
            else:
                industry = text
                location_text = ""
        else:
            industry = ""
            location_text = ""
        return industry, location_text

    def _parse_job_id(self, card: WebElement, job_url: str) -> str:
        """Extract job ID"""
        job_id = card.get_attribute('data-occludable-job-id')
        if not job_id and '/view/' in job_url:
            job_id = job_url.split('/view/')[1].split('/')[0].split('?')[0]
        elif not job_id:
            job_id = job_url.split('/')[-1].split('?')[0]
        return job_id

    def _parse_job_title(self, job_link_elem: WebElement) -> str:
        """Extract job title"""
        try:
            job_title_elem = job_link_elem.find_element(By.CSS_SELECTOR, SELECTORS['job_title'])
            return job_title_elem.text.strip()
        except:
            return job_link_elem.get_attribute('aria-label').replace(' with verification', '').strip()

    def _parse_job_posted_time(self, card: WebElement) -> tuple[str, str]:
        """Extract job posted time and datetime"""
        try:
            time_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_time'])
            posted_time = time_elem.text.strip()
            posted_datetime = time_elem.get_attribute('datetime')
            return posted_time, posted_datetime
        except:
            return "", ""

    def _parse_job_flags(self, card: WebElement) -> tuple[bool, bool]:
        """Extract job flags (promoted, easy apply)"""
        try:
            promoted_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_promoted'])
            is_promoted = "Promoted" in promoted_elem.text
        except:
            is_promoted = False

        try:
            card.find_element(By.CSS_SELECTOR, SELECTORS['job_easy_apply'])
            easy_apply = True
        except:
            easy_apply = False

        return is_promoted, easy_apply

    def parse_profile_from_search(self, element: WebElement, keywords: str, location: Optional[str] = None) -> Optional[
        ProfileData]:
        """Parse profile data from search result element"""
        try:
            profile_url = self._parse_profile_url(element)
            if not profile_url:
                return None

            return ProfileData(
                profile_url=profile_url,
                name=self._parse_profile_name(element),
                headline=self._extract_text(element, 'div.t-14.t-black.t-normal'),
                location=self._parse_profile_location(element),
                search_keywords=keywords,
                search_location=location
            )
        except Exception as e:
            logger.debug(f"Error parsing profile from search: {e}")
            return None

    def parse_company_from_search(self, element: WebElement, keywords: str, location: Optional[str] = None) -> Optional[
        CompanyData]:
        """Parse company data from search result element"""
        try:
            company_url = self._parse_company_url(element)
            if not company_url:
                return None

            company_link_elem = self._find_element_by_selectors(element, SELECTORS['company_link'])
            industry, location_text = self._parse_industry_location(element)

            return CompanyData(
                company_url=company_url,
                company_id=self._parse_company_id(element),
                name=self._parse_company_name(element, company_link_elem),
                industry=industry,
                location=location_text,
                company_size=self._extract_text(element, SELECTORS['company_size']),
                summary=self._extract_text(element, SELECTORS.get('company_summary', [])),
                search_keywords=keywords,
                search_location=location
            )
        except Exception as e:
            logger.debug(f"Error parsing company from search: {e}")
            return None

    def parse_job_from_search(self, card: WebElement, keywords: str, location: Optional[str] = None) -> Optional[
        JobData]:
        """Parse job data from search result card"""
        try:
            job_link_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['job_link'])
            job_url = job_link_elem.get_attribute('href')
            job_id = self._parse_job_id(card, job_url)
            posted_time, posted_datetime = self._parse_job_posted_time(card)
            is_promoted, easy_apply = self._parse_job_flags(card)

            return JobData(
                job_id=job_id,
                job_url=job_url,
                title=self._parse_job_title(job_link_elem),
                company=self._extract_text(card, SELECTORS['job_company']),
                location=self._extract_text(card, SELECTORS['job_location']),
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
        """Save parsed data to JSON files"""
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
