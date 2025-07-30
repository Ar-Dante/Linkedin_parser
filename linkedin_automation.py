import asyncio
import json
from typing import Optional
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc

from base_automatation import BaseAutomation
from models import ConversationData
from config import *
from utils import *

logger = logging.getLogger(__name__)


class LinkedInAutomation(BaseAutomation):
    """LinkedIn automation with async support"""

    def __init__(self, use_proxy: bool = True):
        super().__init__()
        self.use_proxy = use_proxy
        self.conversations: dict[str, ConversationData] = {}
        self.cookies_path = os.path.join(SESSION_FOLDER, COOKIES_FILE)
        self.user_agent_path = os.path.join(SESSION_FOLDER, USER_AGENT_FILE)

    async def setup_driver(self) -> None:
        """Initialize Chrome driver with anti-detection features"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')

        user_agent = await self._get_or_create_user_agent()
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        if self.use_proxy and PROXY_LIST:
            proxy = random.choice(PROXY_LIST)
            if await self._check_proxy(proxy):
                options.add_argument(f'--proxy-server={proxy}')
                logger.info(f"Using proxy: {proxy}")

        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def login(self) -> bool:
        """Login to LinkedIn with session management"""
        try:
            if REUSE_SESSION and await self._load_cookies():
                self.driver.get(f"{LINKEDIN_URL}/feed/")
                await asyncio.sleep(random.uniform(3, 5))

                if await self._is_logged_in():
                    self.logged_in = True
                    logger.info("Successfully logged in using saved session")
                    return True

            return await self._perform_login()

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def send_connection_request(self, profile_url: str, message: str = CONNECTION_MESSAGE,
                                      note_required: bool = True) -> bool:
        """Send connection request with optional personalized message"""
        if not self.logged_in:
            logger.error("Not logged in!")
            return False

        try:
            logger.info(f"Sending connection request to: {profile_url}")

            if self.driver.current_url != profile_url:
                self.driver.get(profile_url)
                await asyncio.sleep(random.uniform(3, 5))

            more_button = self.wait_for_element(SELECTORS['more_button'])
            if not more_button:
                logger.error("More button not found")
                return False

            await self._safe_click(more_button)
            await asyncio.sleep(random.uniform(1, 2))

            connect_button = self.wait_for_element(SELECTORS['connect_button_dropdown'])
            if not connect_button:
                logger.error("Connect button not found in dropdown menu")
                return False

            await self._safe_click(connect_button)
            await asyncio.sleep(random.uniform(2, 3))

            if note_required:
                add_note_button = self.wait_for_element(SELECTORS['add_note_button'], timeout=5)
                if add_note_button:
                    await self._safe_click(add_note_button)
                    await asyncio.sleep(random.uniform(1, 2))

                    message_textarea = self.wait_for_element(SELECTORS['custom_message_textarea'], timeout=5)
                    if message_textarea:
                        await self._human_typing(message_textarea, message)
                        await asyncio.sleep(random.uniform(1, 2))

            send_button = self.wait_for_element(SELECTORS['send_invitation_button'], timeout=5)
            if not send_button:
                logger.error("Send invitation button not found")
                return False

            await self._safe_click(send_button)
            logger.info("Connection request sent successfully!")

            await self._update_profile_data(profile_url, {'connection_sent': True,
                                                          'connection_sent_at': time.strftime('%Y-%m-%d %H:%M:%S')})
            await asyncio.sleep(random.uniform(2, 4))
            return True

        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            return False

    async def send_message(self, profile_url: str, message: str = DEFAULT_MESSAGE) -> bool:
        """Send message to a LinkedIn user"""
        if not self.logged_in:
            logger.error("Not logged in!")
            return False

        try:
            logger.info(f"Sending message to: {profile_url}")

            self.driver.get(profile_url)
            await asyncio.sleep(random.uniform(*DELAY_RANGE))

            await self._random_scroll()

            message_button = self.wait_for_element(SELECTORS['message_button'], timeout=15)
            if not message_button:
                logger.error("Message button not found")
                return False

            await self._safe_click(message_button)
            await asyncio.sleep(random.uniform(3, 5))

            message_input = self.wait_for_element(SELECTORS['message_input'], timeout=15)
            if not message_input:
                logger.error("Message input not found")
                return False

            await self._safe_click(message_input)
            await asyncio.sleep(random.uniform(1, 2))

            await self._human_typing(message_input, message)
            await asyncio.sleep(random.uniform(2, 3))

            send_button = self.wait_for_element(SELECTORS['send_button'])
            if not send_button:
                logger.error("Send button not found")
                return False

            await self._safe_click(send_button)
            logger.info("Message sent successfully!")

            user_name = await self._extract_username(profile_url)
            self.conversations[profile_url] = ConversationData(
                message_sent=message,
                timestamp=time.time(),
                has_response=False,
                user_name=user_name
            )

            await asyncio.sleep(random.uniform(2, 4))
            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def send_voice_message(self, profile_url: str, voice_file_path: str = VOICE_MESSAGE_PATH) -> bool:
        """Send voice message to a LinkedIn user"""
        if not self.logged_in:
            logger.error("Not logged in!")
            return False

        if not voice_file_path or not os.path.exists(voice_file_path):
            logger.error(f"Voice file not found: {voice_file_path}")
            return False

        try:
            logger.info(f"Sending voice message to: {profile_url}")

            self.driver.get(profile_url)
            await asyncio.sleep(random.uniform(*DELAY_RANGE))

            await self._random_scroll()

            message_button = self.wait_for_element(SELECTORS['message_button'], timeout=15)
            if not message_button:
                logger.error("Message button not found")
                return False

            await self._safe_click(message_button)
            await asyncio.sleep(random.uniform(3, 5))

            attachment_button = self.find_element_by_selectors(self.driver, SELECTORS['attachment_button'])
            if not attachment_button:
                logger.error("Attachment button not found")
                return False

            await self._safe_click(attachment_button)
            await asyncio.sleep(random.uniform(2, 3))

            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['file_input'])
            if not file_inputs:
                logger.error("File input not found")
                return False

            file_inputs[0].send_keys(os.path.abspath(voice_file_path))
            logger.info(f"Uploaded voice file: {voice_file_path}")
            await asyncio.sleep(random.uniform(3, 5))

            send_button = self.wait_for_element(SELECTORS['send_button'], timeout=10)
            if not send_button:
                logger.error("Send button not found after file upload")
                return False

            await self._safe_click(send_button)
            logger.info("Voice message sent successfully!")

            user_name = await self._extract_username(profile_url)
            self.conversations[profile_url] = ConversationData(
                message_sent='[Voice Message]',
                timestamp=time.time(),
                has_response=False,
                user_name=user_name,
                voice_sent=True
            )

            await asyncio.sleep(random.uniform(2, 4))
            return True

        except Exception as e:
            logger.error(f"Error sending voice message: {e}")
            return False

    async def check_response(self, profile_url: str) -> Optional[bool]:
        """Check if user has responded to the message"""
        if profile_url not in self.conversations:
            logger.warning(f"No conversation found for {profile_url}")
            return None

        try:
            logger.info(f"Checking response for: {profile_url}")
            self.driver.get(f"{LINKEDIN_URL}/messaging/")
            await asyncio.sleep(random.uniform(*DELAY_RANGE))

            conversations = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['conversation_list'])

            for conv in conversations[:20]:
                try:
                    unread_badges = conv.find_elements(By.CSS_SELECTOR, SELECTORS['unread_badge'])
                    if not unread_badges:
                        continue

                    participant_element = conv.find_element(By.CSS_SELECTOR, SELECTORS['participant_name'])
                    participant_name = participant_element.text.strip()

                    tracked_name = self.conversations[profile_url].user_name
                    if participant_name.lower() != tracked_name.lower():
                        continue

                    await self._safe_click(conv)
                    await asyncio.sleep(random.uniform(2, 3))

                    voice_messages = await self._find_voice_messages()
                    if voice_messages:
                        logger.info(f"Found {len(voice_messages)} voice message(s) from {participant_name}")
                        downloaded = await self.download_voice_messages(self.driver)
                        if downloaded:
                            self.conversations[profile_url].voice_responses = downloaded

                    messages = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['last_message'])
                    if messages:
                        last_message = messages[-1].text

                        if last_message != self.conversations[profile_url].message_sent:
                            self.conversations[profile_url].has_response = True
                            logger.info(f"Response received from {participant_name} ({profile_url})")
                            return True

                    if voice_messages:
                        self.conversations[profile_url].has_response = True
                        logger.info(f"Voice response received from {participant_name} ({profile_url})")
                        return True

                except Exception as e:
                    logger.debug(f"Error checking conversation: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"Error checking response: {e}")
            return None

    async def download_voice_messages(self, conversation_element) -> list[str]:
        """Download voice messages from a conversation"""
        downloaded_files = []

        try:
            os.makedirs(DOWNLOAD_PATH, exist_ok=True)

            audio_elements = await self._find_voice_messages()

            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])

            for i, audio in enumerate(audio_elements):
                try:
                    audio_src = audio.get_attribute('src')
                    if not audio_src:
                        continue

                    timestamp = int(time.time())
                    filename = f"voice_message_{timestamp}_{i}.mp3"
                    filepath = os.path.join(DOWNLOAD_PATH, filename)

                    headers = {
                        'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
                        'Referer': 'https://www.linkedin.com/'
                    }
                    response = session.get(audio_src, headers=headers, stream=True)

                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        logger.info(f"Downloaded voice message: {filename}")
                        downloaded_files.append(filepath)

                        await asyncio.sleep(random.uniform(1, 2))
                    else:
                        logger.error(f"Failed to download voice message: {response.status_code}")

                except Exception as e:
                    logger.error(f"Error downloading individual voice message: {e}")
                    continue

            return downloaded_files

        except Exception as e:
            logger.error(f"Error in download_voice_messages: {e}")
            return downloaded_files

    async def run_response_checker(self, profile_urls: list[str], interval: int = CHECK_INTERVAL) -> None:
        """Continuously check for responses"""
        logger.info(f"Starting response checker with {interval}s interval")

        while True:
            try:
                for profile_url in profile_urls:
                    if profile_url in self.conversations and not self.conversations[profile_url].has_response:
                        has_response = await self.check_response(profile_url)
                        if has_response:
                            logger.info(f"New response from {profile_url}!")

                            voice_files = self.conversations[profile_url].voice_responses
                            if voice_files:
                                logger.info(f"Downloaded {len(voice_files)} voice messages")

                        await asyncio.sleep(random.uniform(30, 60))

                logger.info(f"Waiting {interval} seconds before next check...")
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Response checker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in response checker: {e}")
                await asyncio.sleep(60)

    async def close(self) -> None:
        """Close the browser and save session"""
        if self.driver:
            if self.logged_in and REUSE_SESSION:
                await self._save_cookies()
            self.driver.quit()
            logger.info("Browser closed")

    # Private helper methods
    async def _get_or_create_user_agent(self) -> str:
        """Get or create user agent"""
        if os.path.exists(self.user_agent_path):
            with open(self.user_agent_path, 'r') as f:
                return f.read().strip()
        else:
            user_agent = get_random_user_agent()
            with open(self.user_agent_path, 'w') as f:
                f.write(user_agent)
            return user_agent

    async def _check_proxy(self, proxy: str) -> bool:
        """Check if proxy is working"""
        return check_proxy(proxy)

    async def _save_cookies(self) -> bool:
        """Save browser cookies"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Saved {len(cookies)} cookies")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False

    async def _load_cookies(self) -> bool:
        """Load cookies from file"""
        try:
            if not os.path.exists(self.cookies_path):
                return False

            self.driver.get(LINKEDIN_URL)
            await asyncio.sleep(random.uniform(2, 3))

            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie['expiry']
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass

            self.driver.refresh()
            await asyncio.sleep(random.uniform(3, 5))
            return True

        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    async def _is_logged_in(self) -> bool:
        """Check if logged in"""
        try:
            current_url = self.driver.current_url
            if any(path in current_url for path in ['feed', 'mynetwork', 'messaging', 'jobs']):
                profile_elements = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['profile_photo'])
                return bool(profile_elements)
            return False
        except:
            return False

    async def _perform_login(self) -> bool:
        """Perform actual login"""
        logger.info("Starting login process...")
        self.driver.get(LOGIN_URL)
        await asyncio.sleep(random.uniform(*DELAY_RANGE))

        email_input = self.wait_for_element(SELECTORS['email_input'])
        if not email_input:
            raise Exception("Email input not found")

        await self._human_typing(email_input, LINKEDIN_EMAIL)
        await asyncio.sleep(random.uniform(1, 2))

        password_input = self.wait_for_element(SELECTORS['password_input'])
        if not password_input:
            raise Exception("Password input not found")

        await self._human_typing(password_input, LINKEDIN_PASSWORD)
        await asyncio.sleep(random.uniform(1, 2))

        login_button = self.wait_for_element(SELECTORS['login_button'])
        if not login_button:
            raise Exception("Login button not found")

        await self._safe_click(login_button)
        await asyncio.sleep(random.uniform(5, 8))

        if await self._handle_verification():
            await asyncio.sleep(random.uniform(3, 5))

        if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
            self.logged_in = True
            logger.info("Login successful!")
            await self._save_cookies()
            await self._random_scroll()
            return True

        return False

    async def _handle_verification(self) -> bool:
        """Handle verification if required"""
        if "checkpoint" not in self.driver.current_url and "challenge" not in self.driver.current_url:
            return False

        logger.info("Verification required!")
        await asyncio.sleep(random.uniform(2, 3))

        verification_input = self.wait_for_element(SELECTORS['verification_inputs'], timeout=5)
        if not verification_input:
            return False

        code = await self._get_verification_code()
        if not code:
            return False

        await self._human_typing(verification_input, code)
        await asyncio.sleep(random.uniform(1, 2))

        submit_button = self.wait_for_element(SELECTORS['verification_submit'], timeout=5)
        if submit_button:
            await self._safe_click(submit_button)
        else:
            verification_input.send_keys(Keys.RETURN)

        logger.info("Verification code submitted")
        await asyncio.sleep(random.uniform(3, 5))
        return True

    async def _get_verification_code(self) -> Optional[str]:
        """Get verification code from user"""
        logger.info("Manual verification required!")
        print("Please enter the verification code sent to your email/phone:")

        try:
            code = await asyncio.get_event_loop().run_in_executor(None, input, "Enter verification code: ")
            return code.strip() if code else None
        except:
            return None

    async def _find_voice_messages(self) -> list:
        """Find voice message elements"""
        for selector in SELECTORS['voice_messages']:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements
        return []

    async def _safe_click(self, element) -> bool:
        """Safely click an element"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            await asyncio.sleep(random.uniform(0.5, 1))
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as e:
                logger.error(f"Failed to click element: {e}")
                return False

    async def _human_typing(self, element, text: str) -> None:
        """Type with human-like speed"""
        element.clear()
        for char in text:
            element.send_keys(char)
            await asyncio.sleep(random.uniform(*TYPING_DELAY))

    async def _random_scroll(self, scrolls: int = None) -> None:
        """Perform random scrolling"""
        if scrolls is None:
            scrolls = random.randint(1, 3)

        for _ in range(scrolls):
            scroll_height = random.randint(300, 700)
            direction = random.choice([1, -1])
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height * direction})")
            await asyncio.sleep(random.uniform(1, 2))

    async def _extract_username(self, profile_url: str) -> str:
        """Extract username from profile"""
        try:
            name_elem = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['profile_name'])
            return name_elem.text.strip()
        except:
            return profile_url.split('/')[-2]

    async def _update_profile_data(self, profile_url: str, update_data: dict) -> bool:
        """Update profile data in storage"""
        try:
            filepath = os.path.join(DATA_FOLDER, PROFILES_FILE)

            profiles = {}
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    if isinstance(profiles, list):
                        profiles = {p['profile_url']: p for p in profiles}

            if profile_url not in profiles:
                profiles[profile_url] = {'profile_url': profile_url}

            profiles[profile_url].update(update_data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Error updating profile data: {e}")
            return False
