import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # App Settings
    APP_NAME = "LinkedIn Scraper"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # LinkedIn Credentials
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", 3600))  # 1 hour

    # Scraper Settings
    KEYWORDS = ["data governance", "data lineage", "metadata management"]
    MAX_POSTS_PER_KEYWORD = 10
    MAX_SCROLL_ATTEMPTS = 3
    SCROLL_PAUSE_TIME = 3

    # Selenium Settings
    SELENIUM_TIMEOUT = 10
    CHROME_OPTIONS = [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1920,1080",
        "--disable-application-cache",
        "--disable-cache",
        "--disable-extensions"
    ]

settings = Settings() 