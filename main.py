import asyncio
import logging
import sys
from linkedin_automation import LinkedInAutomation
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from search_engine import SearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for LinkedIn automation"""

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.error("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
        sys.exit(1)

    automation = LinkedInAutomation(use_proxy=True)


    try:
        await automation.setup_driver()
        search_engine = SearchEngine(automation)
        if not await automation.login():
            logger.error("Failed to login")
            return

        # # Search for people
        people_results = await search_engine.search_people(
            keywords="AI developer Spain",
            max_results=20
        )
        logger.info(f"Found {len(people_results)} profiles")

        # Search for companies
        company_results = await search_engine.search_companies(
            keywords="AI artificial intelligence Spain",
            max_results=20
        )
        logger.info(f"Found {len(company_results)} companies")

        # Search for jobs
        job_results = await search_engine.search_jobs(
            keywords="AI engineer",
            location="Spain",
            max_results=20
        )
        logger.info(f"Found {len(job_results)} jobs")

        # Send connection request
        if True:
            # profile = people_results[0]
            message = f"Hi ! I noticed you work in AI development. I'd love to connect."

            success = await automation.send_connection_request(
                "https://www.linkedin.com/in/fabriciocarraro",
                message
            )

            if success:
                logger.info(f"Connection request sent to ")
            else:
                logger.error(f"Failed to send connection request")

        # Send text message to existing connection
        success = await automation.send_message(
            "https://www.linkedin.com/in/artem-danilov-871847283/",
            "Hi! I came across your profile and would love to connect."
        )

        if success:
            logger.info("Message sent successfully")
        else:
            logger.error("Failed to send message")

        # Send voice message example
        # success = await automation.send_voice_message(
        #     "https://www.linkedin.com/in/artem-danilov-871847283/",
        #     "./voice_message.mp3"
        # )

        profile_urls = ["https://www.linkedin.com/in/artem-danilov-871847283/"]
        await automation.run_response_checker(profile_urls)

    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await automation.close()


if __name__ == "__main__":
    asyncio.run(main())
