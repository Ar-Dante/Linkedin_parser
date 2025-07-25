import logging
import sys
from linkedin_automation import LinkedInAutomation
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for LinkedIn automation"""
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.error("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
        sys.exit(1)

    automation = LinkedInAutomation(use_proxy=True)

    try:
        automation.setup_driver()

        if not automation.login():
            logger.error("Failed to login")
            return

        profile_urls = [
            "https://www.linkedin.com/in/artem-danilov-871847283/",
        ]

        for profile_url in profile_urls:
            success = automation.send_message(
                profile_url,
                "Hi! I came across your profile and would love to connect."
            )
            if success:
                logger.info(f"Message sent to {profile_url}")
            else:
                logger.error(f"Failed to send message to {profile_url}")

        automation.run_response_checker(profile_urls)

    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        automation.close()


if __name__ == "__main__":
    main()
