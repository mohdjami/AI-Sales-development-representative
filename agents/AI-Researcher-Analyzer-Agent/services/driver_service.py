import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import time
import random

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class LinkedInDriver:
    _instance = None
    _driver = None
    _last_login = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Created new LinkedInDriver instance")
        return cls._instance
    
    def get_driver(self):
        if self._driver is None or self._needs_login():
            logger.info("Setting up new WebDriver instance")
            self._setup_driver()
        return self._driver
    
    def _needs_login(self):
        needs_login = (self._last_login is None or 
                      datetime.now() - self._last_login > timedelta(hours=23))
        if needs_login:
            logger.info("Login session expired or not initialized")
        return needs_login
    
    def _setup_driver(self):
        try:
            if self._driver:
                logger.debug("Quitting existing WebDriver instance")
                try:
                    self._driver.quit()
                except Exception as e:
                    logger.error(f"Error quitting driver: {str(e)}")
            
            logger.info("Initializing undetected-chromedriver")
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-notifications')
            
            # Initialize undetected-chromedriver
            self._driver = uc.Chrome(options=options)
            
            logger.info("Chrome WebDriver initialized successfully")
            self._login()
            
        except Exception as e:
            logger.error(f"Error in _setup_driver: {str(e)}")
            raise
    
    def _login(self):
        try:
            logger.info("Starting LinkedIn login process")
            
            # First visit LinkedIn homepage
            self._driver.get("https://www.linkedin.com")
            time.sleep(random.uniform(2, 4))
            
            # Then go to login page if not already there
            if "login" not in self._driver.current_url:
                self._driver.get("https://www.linkedin.com/login")
                time.sleep(random.uniform(2, 4))

            # Wait for and enter email
            logger.debug("Looking for email input field")
            email_elem = WebDriverWait(self._driver, settings.SELENIUM_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "username"))
            )
            logger.info("Email field found, entering email")
            email_elem.send_keys(settings.LINKEDIN_EMAIL)
            time.sleep(random.uniform(0.5, 1.5))

            # Wait for and enter password
            logger.debug("Looking for password input field")
            password_elem = WebDriverWait(self._driver, settings.SELENIUM_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            logger.info("Password field found, entering password")
            password_elem.send_keys(settings.LINKEDIN_PASSWORD)
            time.sleep(random.uniform(0.5, 1.5))

            # Click login button
            logger.debug("Looking for login button")
            login_button = WebDriverWait(self._driver, settings.SELENIUM_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            logger.info("Login button found, attempting to click")
            login_button.click()
            
            # Wait for successful login with increased timeout
            logger.debug("Waiting for home feed to load")
            try:
                WebDriverWait(self._driver, 30).until(  # Increased timeout to 30 seconds
                    EC.presence_of_element_located((By.CLASS_NAME, "global-nav"))
                )
                logger.info("Login successful - global nav found")
                self._last_login = datetime.now()
                
            except TimeoutException:
                logger.error("Login verification timeout - checking current state")
                current_url = self._driver.current_url
                logger.debug(f"Current URL: {current_url}")
                
                if "checkpoint" in current_url:
                    logger.error("Security checkpoint detected")
                    raise Exception("LinkedIn security checkpoint encountered")
                elif "login" in current_url:
                    logger.error("Still on login page - credentials might be incorrect")
                    raise Exception("Login failed - invalid credentials")
                else:
                    logger.error("Unknown login failure")
                    raise Exception("Login failed - unknown reason")

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise