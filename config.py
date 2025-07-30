import os
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

SESSION_FOLDER = os.getenv('SESSION_FOLDER', './sessions')
COOKIES_FILE = os.getenv('COOKIES_FILE', 'linkedin_cookies.json')
USER_AGENT_FILE = os.getenv('USER_AGENT_FILE', 'user_agent.txt')
REUSE_SESSION = os.getenv('REUSE_SESSION', 'true').lower() == 'true'

os.makedirs(SESSION_FOLDER, exist_ok=True)

PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []

DEFAULT_MESSAGE = os.getenv('DEFAULT_MESSAGE', 'Hello! I would like to connect.')
CONNECTION_MESSAGE = os.getenv('CONNECTION_MESSAGE', 'Hi! I found your profile interesting and would like to connect.')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
VOICE_MESSAGE_PATH = os.getenv('VOICE_MESSAGE_PATH', '')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', './downloads')

DATA_FOLDER = os.getenv('DATA_FOLDER', './data')
PROFILES_FILE = os.getenv('PROFILES_FILE', 'profiles.json')
SEARCH_RESULTS_FILE = os.getenv('SEARCH_RESULTS_FILE', 'search_results.json')
COMPANIES_FILE = os.getenv('COMPANIES_FILE', 'companies.json')
JOBS_FILE = os.getenv('JOBS_FILE', 'jobs.json')

os.makedirs(DATA_FOLDER, exist_ok=True)
if DOWNLOAD_PATH:
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

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
    'verification_inputs': 'input[name="pin"]',
    'verification_submit': 'button[type="submit"]',
    'profile_photo': 'img.global-nav__me-photo',

    'company_link': [
        'a.ksGOyBtVzEzOJgTMnCzNSFpERwCXUapITUY[href*="/company/"]',
        'span.HuxbgxjchZqeihDnhWiTBJohMvlCjkvcWLEUHgF a',
        'a[href*="/company/"]',
        '.entity-result__title-text a'
    ],

    'company_name': [
        'span.HuxbgxjchZqeihDnhWiTBJohMvlCjkvcWLEUHgF',
        'span.HuxbgxjchZqeihDnhWiTBJohMvlCjkvcWLEUHgF a',
        'a.ksGOyBtVzEzOJgTMnCzNSFpERwCXUapITUY',
        '.entity-result__title-text span'
    ],

    'company_industry': [
        'div.MawsxAfWvbBKkrOjaPGMySUURnPsDYo',
        '.entity-result__primary-subtitle',
        'div[class*="t-14 t-black t-normal"]'
    ],

    'company_size': [
        'div.zFrSJzvYksrjrvxvJvLpZwWBZkuYPzRZeQKQU',
        '.entity-result__insights',
        '.reusable-search-simple-insight__text'
    ],

    'company_summary': [
        'p.laFryWCRMKpRvyJvjTeMfXbxGryAiHuzLfPQ',
        '.entity-result__summary--2-lines',
        'p[class*="entity-result__summary"]'
    ],

    'job_cards': [
        'li.scaffold-layout__list-item[data-occludable-job-id]',
        'div.job-card-container'
    ],

    'job_link': 'a.job-card-container__link',
    'job_title': 'strong',
    'job_company': [
        'div.artdeco-entity-lockup__subtitle span',
        '.artdeco-entity-lockup__subtitle'
    ],
    'job_location': [
        'ul.job-card-container__metadata-wrapper li span',
        '.artdeco-entity-lockup__caption span'
    ],
    'job_time': 'time',
    'job_promoted': 'li[class*="footer-item"] span',
    'job_easy_apply': 'span:contains("Easy Apply")',

    'next_page_button': [
        'button[aria-label="Next"]',
        'button.artdeco-pagination__button--next',
        '.artdeco-pagination__button--next'
    ],
    'search_results': [
        'div[data-chameleon-result-urn]',
        'li[class*="ember-view"] div[data-view-name="search-entity-result-universal-template"]',
        'ul[role="list"] > li'
    ],

    'see_more_button': "//button[contains(text(), 'See more') or contains(text(), 'Show more')]",
    'profile_link': 'a[href*="/in/"], a[href*="/search/results/people/headless"]',
    'profile_name': 'span[dir="ltr"] span[aria-hidden="true"]',
    'profile_name_fallback': 'div.t-sans a',
    'profile_headline': 'div.t-14.t-black.t-normal',
    'profile_location': 'div.t-14.t-normal',

    'more_button': 'button[aria-label*="More actions"]',
    'connect_button_dropdown': 'div[aria-label*="Invite"][aria-label*="connect"]',
    'connect_button': 'button[aria-label*="Connect"]',
    'add_note_button': 'button[aria-label*="Add a note"]',
    'custom_message_textarea': 'textarea[name="message"]',
    'send_invitation_button': 'button[aria-label*="Send"]',

    'attachment_button': [
        'button[aria-label*="Attach a file"]',
        'button[aria-label*="Attach"]',
        'button[data-control-name="attachment"]'
    ],
    'file_input': 'input[type="file"]',
    'voice_messages': [
        'audio',
        'div[data-msg-content-type="AUDIO"] audio',
        'div.msg-s-message-group__cards audio'
    ]
}
