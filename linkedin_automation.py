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

    def setup_driver(self) -> None:
        """Initialize Chrome driver with anti-detection features"""

        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent={get_random_user_agent()}')
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

    def login(self) -> bool:
        """Login to LinkedIn account"""
        try:
            logger.info("Starting login process...")
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

                self.conversations[profile_url] = {
                    'message_sent': message,
                    'timestamp': time.time(),
                    'has_response': False
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
            print(conversations)

            for conv in conversations[:20]:
                try:
                    unread_badges = conv.find_elements(By.CSS_SELECTOR, SELECTORS['unread_badge'])
                    print(unread_badges)
                    if not unread_badges:
                        continue

                    participant_element = conv.find_element(By.CSS_SELECTOR, SELECTORS['participant_name'])
                    participant_name = participant_element.text.strip()

                    tracked_name = self.conversations[profile_url].get('user_name', '')
                    if participant_name.lower() != tracked_name.lower():
                        continue

                    safe_click(self.driver, conv)
                    human_delay(2, 3)

                    messages = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['last_message'])
                    if messages:
                        last_message = messages[-1].text

                        if last_message != self.conversations[profile_url]['message_sent']:
                            self.conversations[profile_url]['has_response'] = True
                            logger.info(f"Response received from {participant_name} ({profile_url})")
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
                time.sleep(60)

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
