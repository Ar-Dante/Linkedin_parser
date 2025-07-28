import json
from typing import Optional, List
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from config import *
from utils import *

logger = logging.getLogger(__name__)


class LinkedInAutomation:
    def __init__(self, use_proxy: bool = True):
        self.driver = None
        self.use_proxy = use_proxy
        self.logged_in = False
        self.conversations = {}

        self.cookies_path = os.path.join(SESSION_FOLDER, COOKIES_FILE)
        self.user_agent_path = os.path.join(SESSION_FOLDER, USER_AGENT_FILE)

    def setup_driver(self) -> None:
        """Initialize Chrome driver with anti-detection features"""
        options = uc.ChromeOptions()

        options.add_argument('--disable-blink-features=AutomationControlled')

        if os.path.exists(self.user_agent_path):
            with open(self.user_agent_path, 'r') as f:
                user_agent = f.read().strip()
            logger.info("Using saved user-agent")
        else:
            user_agent = get_random_user_agent()
            with open(self.user_agent_path, 'w') as f:
                f.write(user_agent)
            logger.info("Generated new user-agent")

        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        if self.use_proxy and PROXY_LIST:
            proxy = random.choice(PROXY_LIST)
            if check_proxy(proxy):
                options.add_argument(f'--proxy-server={proxy}')
                logger.info(f"Using proxy: {proxy}")
            else:
                logger.warning(f"Proxy {proxy} is not working, continuing without proxy")

        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def save_cookies(self) -> bool:
        """Save browser cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            print(cookies)
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Cookies saved to {self.cookies_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False

    def load_cookies(self) -> bool:
        """Load cookies from file"""
        try:
            if not os.path.exists(self.cookies_path):
                logger.info(f"No cookies file found at {self.cookies_path}")
                return False

            self.driver.get(LINKEDIN_URL)
            human_delay(2, 3)

            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie['expiry']
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Could not add cookie: {e}")

            logger.info(f"Cookies loaded from {self.cookies_path}")

            self.driver.refresh()
            human_delay(3, 5)

            return True

        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    def is_logged_in(self) -> bool:
        """Check if currently logged in"""
        try:
            current_url = self.driver.current_url
            if any(path in current_url for path in ['feed', 'mynetwork', 'messaging', 'jobs', 'notifications']):
                profile_elements = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['profile_photo'])
                if profile_elements:
                    return True
            return False
        except Exception:
            return False

    def login(self) -> bool:
        """Login to LinkedIn account"""
        try:
            if REUSE_SESSION and self.load_cookies():
                logger.info("Checking if session is still valid...")

                self.driver.get(f"{LINKEDIN_URL}/feed/")
                human_delay(3, 5)

                if self.is_logged_in():
                    self.logged_in = True
                    logger.info(f"Successfully logged in using saved session")
                    return True
                else:
                    logger.info("Saved session is no longer valid, proceeding with login...")

            logger.info(f"Starting login process...")
            self.driver.get(LOGIN_URL)
            human_delay(*DELAY_RANGE)

            email_input = wait_for_element(self.driver, SELECTORS['email_input'])
            if not email_input:
                raise Exception("Email input not found")

            move_to_element_human(self.driver, email_input)
            human_typing(email_input, LINKEDIN_EMAIL, TYPING_DELAY)
            human_delay(1, 2)

            password_input = wait_for_element(self.driver, SELECTORS['password_input'])
            if not password_input:
                raise Exception("Password input not found")

            move_to_element_human(self.driver, password_input)
            human_typing(password_input, LINKEDIN_PASSWORD, TYPING_DELAY)
            human_delay(1, 2)

            login_button = wait_for_element(self.driver, SELECTORS['login_button'])
            if not login_button:
                raise Exception("Login button not found")

            move_to_element_human(self.driver, login_button)
            safe_click(self.driver, login_button)

            human_delay(5, 8)

            if self._handle_verification():
                human_delay(3, 5)

            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                self.logged_in = True
                logger.info("Login successful!")
                logger.info("Save cookie")
                self.save_cookies()

                random_scroll(self.driver, random.randint(1, 3))
                return True
            else:
                logger.error("Login failed - unexpected URL")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _handle_verification(self) -> bool:
        """Handle verification code if required"""
        try:
            if "checkpoint" not in self.driver.current_url and "challenge" not in self.driver.current_url:
                return False

            logger.info("Verification required!")

            human_delay(2, 3)

            verification_input = wait_for_element(self.driver, SELECTORS['verification_inputs'], timeout=5)

            if not verification_input:
                logger.error("Verification input not found")
                return False

            verification_code = self._get_verification_code()
            if not verification_code:
                return False

            move_to_element_human(self.driver, verification_input)
            human_typing(verification_input, verification_code, TYPING_DELAY)
            human_delay(1, 2)

            submit_button = wait_for_element(self.driver, SELECTORS['verification_submit'], timeout=5)

            if submit_button:
                move_to_element_human(self.driver, submit_button)
                safe_click(self.driver, submit_button)
                logger.info("Verification code submitted")
                human_delay(3, 5)
                return True
            else:
                verification_input.send_keys(Keys.RETURN)
                logger.info("Verification code submitted via Enter key")
                human_delay(3, 5)
                return True

        except Exception as e:
            logger.error(f"Verification handling error: {e}")
            return False

    def _get_verification_code(self) -> Optional[str]:
        """Get verification code from user or automated source"""
        logger.info("Manual verification required!")
        print("Please enter the verification code sent to your email/phone:")

        try:
            code = input("Enter verification code: ").strip()
            if code:
                return code
            else:
                logger.error("No verification code provided")
                return None
        except KeyboardInterrupt:
            logger.info("Verification cancelled by user")
            return None

    def send_message(self, profile_url: str, message: str = DEFAULT_MESSAGE) -> bool:
        """Send message to a LinkedIn user"""
        if not self.logged_in:
            logger.error("Not logged in!")
            return False

        try:
            logger.info(f"Navigating to profile: {profile_url}")
            self.driver.get(profile_url)
            human_delay(*DELAY_RANGE)

            random_scroll(self.driver, random.randint(1, 2))

            message_button = wait_for_element(self.driver, SELECTORS['message_button'], 15)
            if not message_button:
                logger.error("Message button not found")
                return False

            move_to_element_human(self.driver, message_button)
            human_delay(1, 2)

            if not safe_click(self.driver, message_button):
                return False

            human_delay(3, 5)

            message_input = wait_for_element(self.driver, SELECTORS['message_input'], 15)
            if not message_input:
                logger.error("Message input not found")
                return False

            move_to_element_human(self.driver, message_input)
            safe_click(self.driver, message_input)
            human_delay(1, 2)

            for char in message:
                message_input.send_keys(char)
                time.sleep(random.uniform(*TYPING_DELAY))

            human_delay(2, 3)

            send_button = wait_for_element(self.driver, SELECTORS['send_button'])
            if not send_button:
                logger.error("Send button not found")
                return False

            move_to_element_human(self.driver, send_button)
            human_delay(1, 2)

            if safe_click(self.driver, send_button):
                logger.info("Message sent successfully!")

                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['profile_name'])
                    user_name = name_element.text.strip()
                except:
                    user_name = profile_url.split('/')[-2]
                self.conversations[profile_url] = {
                    'message_sent': message,
                    'timestamp': time.time(),
                    'has_response': False,
                    'user_name': user_name
                }

                human_delay(2, 4)
                return True

            return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def check_response(self, profile_url: str) -> Optional[bool]:
        """Check if user has responded to the message"""
        if profile_url not in self.conversations:
            logger.warning(f"No conversation found for {profile_url}")
            return None

        try:
            logger.info(f"Checking response for: {profile_url}")
            self.driver.get(f"{LINKEDIN_URL}/messaging/")
            human_delay(*DELAY_RANGE)

            conversations = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['conversation_list'])

            for conv in conversations[:20]:  # Check first 20 conversations
                try:
                    unread_badges = conv.find_elements(By.CSS_SELECTOR, SELECTORS['unread_badge'])
                    if not unread_badges:
                        continue

                    participant_element = conv.find_element(By.CSS_SELECTOR, SELECTORS['participant_name'])
                    participant_name = participant_element.text.strip()

                    tracked_name = self.conversations[profile_url].get('user_name', '')
                    if participant_name.lower() != tracked_name.lower():
                        continue

                    safe_click(self.driver, conv)
                    human_delay(2, 3)

                    voice_messages = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['voice_messages'])
                    if voice_messages:
                        logger.info(f"Found {len(voice_messages)} voice message(s) from {participant_name}")
                        downloaded = self.download_voice_messages(self.driver)
                        if downloaded:
                            self.conversations[profile_url]['voice_responses'] = downloaded

                    messages = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['last_message'])
                    if messages:
                        last_message = messages[-1].text

                        if last_message != self.conversations[profile_url]['message_sent']:
                            self.conversations[profile_url]['has_response'] = True
                            logger.info(f"Response received from {participant_name} ({profile_url})")
                            return True

                    if voice_messages:
                        self.conversations[profile_url]['has_response'] = True
                        logger.info(f"Voice response received from {participant_name} ({profile_url})")
                        return True

                except Exception as e:
                    logger.debug(f"Error checking conversation: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"Error checking response: {e}")
            return None

    def run_response_checker(self, profile_urls: List[str], interval: int = CHECK_INTERVAL) -> None:
        """Continuously check for responses"""
        logger.info(f"Starting response checker with {interval}s interval")

        while True:
            try:
                for profile_url in profile_urls:
                    if profile_url in self.conversations and not self.conversations[profile_url]['has_response']:
                        has_response = self.check_response(profile_url)
                        if has_response:
                            logger.info(f"New response from {profile_url}!")

                        human_delay(30, 60)

                logger.info(f"Waiting {interval} seconds before next check...")
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Response checker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in response checker: {e}")
                time.sleep(60)  # Wait before retry

    def send_voice_message(self, profile_url: str, voice_file_path: str = VOICE_MESSAGE_PATH) -> bool:
        """Send voice message to a LinkedIn user"""
        if not self.logged_in:
            logger.error("Not logged in!")
            return False

        if not voice_file_path or not os.path.exists(voice_file_path):
            logger.error(f"Voice file not found: {voice_file_path}")
            return False

        try:
            logger.info(f"Navigating to profile: {profile_url}")
            self.driver.get(profile_url)
            human_delay(*DELAY_RANGE)

            random_scroll(self.driver, random.randint(1, 2))

            message_button = wait_for_element(self.driver, SELECTORS['message_button'], 15)
            if not message_button:
                logger.error("Message button not found")
                return False

            move_to_element_human(self.driver, message_button)
            human_delay(1, 2)

            if not safe_click(self.driver, message_button):
                return False

            human_delay(3, 5)

            attachment_button = wait_for_element(self.driver, SELECTORS['attachment_button'], 15)
            if not attachment_button:
                logger.error("Attachment button not found")
                return False

            move_to_element_human(self.driver, attachment_button)
            human_delay(1, 2)
            safe_click(self.driver, attachment_button)
            human_delay(2, 3)

            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            if not file_inputs:
                logger.error("File input not found")
                return False

            file_input = file_inputs[0]
            file_input.send_keys(os.path.abspath(voice_file_path))
            logger.info(f"Uploaded voice file: {voice_file_path}")
            human_delay(3, 5)

            send_button = wait_for_element(self.driver, SELECTORS['send_button'], 10)
            if not send_button:
                logger.error("Send button not found after file upload")
                return False

            move_to_element_human(self.driver, send_button)
            human_delay(1, 2)

            if safe_click(self.driver, send_button):
                logger.info("Voice message sent successfully!")

                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['profile_name'])
                    user_name = name_element.text.strip()
                except:
                    user_name = profile_url.split('/')[-2]

                self.conversations[profile_url] = {
                    'message_sent': '[Voice Message]',
                    'timestamp': time.time(),
                    'has_response': False,
                    'user_name': user_name,
                    'voice_sent': True
                }

                human_delay(2, 4)
                return True

            return False

        except Exception as e:
            logger.error(f"Error sending voice message: {e}")
            return False

    def download_voice_messages(self, conversation_element) -> List[str]:
        """Download voice messages from a conversation"""
        downloaded_files = []

        try:
            os.makedirs(DOWNLOAD_PATH, exist_ok=True)

            audio_elements = conversation_element.find_elements(By.CSS_SELECTOR, SELECTORS['voice_messages'])

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

                        time.sleep(random.uniform(1, 2))
                    else:
                        logger.error(f"Failed to download voice message: {response.status_code}")

                except Exception as e:
                    logger.error(f"Error downloading individual voice message: {e}")
                    continue

            return downloaded_files

        except Exception as e:
            logger.error(f"Error in download_voice_messages: {e}")
            return downloaded_files

    def run_response_checker(self, profile_urls: List[str], interval: int = CHECK_INTERVAL) -> None:
        """Continuously check for responses"""
        logger.info(f"Starting response checker with {interval}s interval")

        while True:
            try:
                for profile_url in profile_urls:
                    if profile_url in self.conversations and not self.conversations[profile_url]['has_response']:
                        has_response = self.check_response(profile_url)
                        if has_response:
                            logger.info(f"New response from {profile_url}!")

                            # Log voice messages if any
                            voice_files = self.conversations[profile_url].get('voice_responses', [])
                            if voice_files:
                                logger.info(f"Downloaded {len(voice_files)} voice messages")

                        human_delay(30, 60)

                logger.info(f"Waiting {interval} seconds before next check...")
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Response checker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in response checker: {e}")
                time.sleep(60)

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            if self.logged_in and REUSE_SESSION:
                logger.info("Save cookie")
                self.save_cookies()
            self.driver.quit()
            logger.info("Browser closed")
