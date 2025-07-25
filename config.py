import os
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []

DEFAULT_MESSAGE = os.getenv('DEFAULT_MESSAGE', 'Hello! I would like to connect.')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 15))

DELAY_RANGE = (2, 5)
TYPING_DELAY = (0.1, 0.3)
SCROLL_PAUSE = (1, 3)

LINKEDIN_URL = 'https://www.linkedin.com'
LOGIN_URL = f'{LINKEDIN_URL}/login'

SELECTORS = {
    'email_input': 'input[id="username"]',
    'password_input': 'input[id="password"]',
    'login_button': 'button[type="submit"]',
    'message_button': 'button[aria-label*="Message"]',
    'message_input': 'div[role="textbox"][contenteditable="true"]',
    'send_button': 'button.msg-form__send-button[type="submit"]',
    'conversation_list': 'ul.msg-conversations-container__conversations-list li.msg-conversation-listitem',
    'last_message': 'div[data-event-urn*="message"] p',
    'unread_badge': 'span.notification-badge',
    'participant_name': 'h3.msg-conversation-listitem__participant-names span.truncate',
    'profile_name': 'h1.text-heading-xlarge',
    'verification_inputs': 'input[name="pin"]',
    'verification_submit': 'button[type="submit"]'
}
