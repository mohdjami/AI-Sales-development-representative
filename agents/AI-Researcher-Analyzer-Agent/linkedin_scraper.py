import os
import time
import json
from typing import List, Dict, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from dotenv import load_dotenv
import hashlib
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
import pickle
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel
import random
import requests
from urllib.parse import quote_plus

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info(os.getenv("LINKEDIN_PASSWORD"))
# Configure Redis
redis_client = Redis(host=os.getenv("REDIS_HOST"), 
                    port=6379, 
                    db=0,
                    password=os.getenv("REDIS_PASSWORD"),
                    ssl=True,
                    decode_responses=True
                    )

CACHE_EXPIRY = 3600  # 1 hour

# Singleton WebDriver
class LinkedInDriver:
    _instance = None
    _driver = None
    _last_login = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_driver(self):
        if self._driver is None or self._needs_login():
            self._setup_driver()
        return self._driver
    
    def _needs_login(self):
        return (self._last_login is None or 
                datetime.now() - self._last_login > timedelta(hours=23))
    
    def _setup_driver(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {str(e)}")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Create a new user profile directory to avoid cached data
        options.add_argument("user-data-dir=/tmp/chrome-user-data")  # Temporary directory for user data
        options.add_argument("--disable-application-cache")  # Disable application cache
        options.add_argument("--disable-cache")  # Disable cache
        options.add_argument("--disable-extensions")  # Disable extensions

        self._driver = webdriver.Chrome(options=options)
        self._login()
        self._last_login = datetime.now()
    
    def _login(self):
        try:
            self._driver.get("https://www.linkedin.com/login")
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(os.getenv("LINKEDIN_EMAIL"))
            
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            ).send_keys(os.getenv("LINKEDIN_PASSWORD"))
            
            self._driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)
            
            if "feed" not in self._driver.current_url:
                raise Exception("Login failed")
                
            logger.info("Successfully logged in to LinkedIn")
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

class PostCache:
    @staticmethod
    def get_cache_key(keyword: str, page: int) -> str:
        return f"linkedin_posts:{keyword}:{page}"
    
    @staticmethod
    def get_posts(keyword: str, page: int) -> Optional[List[Dict]]:
        cache_key = PostCache.get_cache_key(keyword, page)
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    @staticmethod
    def save_posts(keyword: str, page: int, posts: List[Dict]):
        cache_key = PostCache.get_cache_key(keyword, page)
        redis_client.setex(
            cache_key,
            CACHE_EXPIRY,
            json.dumps(posts)
        )
    
    @staticmethod
    def get_seen_hashes(keyword: str) -> Set[str]:
        seen_key = f"seen_hashes:{keyword}"
        seen_hashes = redis_client.smembers(seen_key)
        return seen_hashes if seen_hashes else set()
    
    @staticmethod
    def add_seen_hash(keyword: str, post_hash: str):
        seen_key = f"seen_hashes:{keyword}"
        redis_client.sadd(seen_key, post_hash)
        redis_client.expire(seen_key, CACHE_EXPIRY)

# API Models
class SearchRequest(BaseModel):
    keywords: List[str]
    page: int = 1
    limit: int = 10

app = FastAPI()

# Load LinkedIn Credentials
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Validate credentials
if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
    logger.error("LinkedIn credentials not found in environment variables")
    raise ValueError("LinkedIn credentials must be set in environment variables")

# Keywords related to Atlan
KEYWORDS = ["data governance", "data lineage", "metadata management"]

def setup_driver() -> webdriver.Chrome:
    """Setup and configure Chrome WebDriver"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
        raise

def login_to_linkedin(driver: webdriver.Chrome) -> bool:
    """
    Logs into LinkedIn with stored credentials
    Returns: bool indicating success/failure
    """
    try:
        logger.info("Attempting to log in to LinkedIn")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for elements to be present
        wait = WebDriverWait(driver, 10)
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        
        # Input credentials
        email_field.clear()
        email_field.send_keys(LINKEDIN_EMAIL)
        password_field.clear()
        password_field.send_keys(LINKEDIN_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(5)
        
        # Verify login success
        if "feed" in driver.current_url:
            logger.info("Successfully logged in to LinkedIn")
            return True
        else:
            logger.error("Login unsuccessful - incorrect URL after login attempt")
            return False
            
    except TimeoutException:
        logger.error("Timeout while waiting for login elements")
        raise
    except Exception as e:
        logger.error(f"Error during LinkedIn login: {str(e)}")
        raise

def get_post_hash(post: Dict) -> str:
    """Generate a unique hash for a post to prevent duplicates"""
    content = f"{post['author']}{post['company']}{post['post']}"
    return hashlib.md5(content.encode()).hexdigest()

def extract_post_data(post_element) -> Optional[Dict]:
    """Extract structured data from a post element"""
    try:
        logger.debug("Extracting data from post element")
        
        # Find author information - multiple possible selectors
        author = "Unknown"
        # Get profile URL and username
        profile_url = ""
        username = ""
        profile_selectors = [
            "a.app-aware-link[href*='/in/']",  # Direct profile links
            "a.feed-shared-actor__container-link",
            "a.update-components-actor__container-link",
            ".feed-shared-actor__title a",
            ".update-components-actor__title a",
            "a[data-tracking-control-name='feed_actor']",
            ".feed-shared-actor__name a",
            ".update-components-actor__name a"
        ]
        # Try to find profile link first
        for selector in profile_selectors:
            profile_element = post_element.select_one(selector)
            if profile_element and 'href' in profile_element.attrs:
                href = profile_element['href']
                if '/in/' in href:
                    profile_url = href
                    # Extract username more robustly
                    try:
                        # Handle both full URLs and relative paths
                        parts = href.split('/in/')
                        if len(parts) > 1:
                            username = parts[1].split('/')[0].split('?')[0]
                            # If we find a username but no author, use username as author
                            if author == "Unknown":
                                author = profile_element.get_text(strip=True) or username
                            break
                    except Exception as e:
                        logger.debug(f"Error extracting username from URL {href}: {str(e)}")
                        continue

        author_selectors = [
            "span.feed-shared-actor__title",
            "span.update-components-actor__name",
            "span.feed-shared-actor__name",
            "a.feed-shared-actor__container-link",
            "a.update-components-actor__container-link",
            "span.update-components-actor__title",
            "a.app-aware-link span",  # New selector for profile links
            ".feed-shared-actor__name", # Direct class selector
            ".update-components-actor__name"  # Direct class selector
        ]
        
        for selector in author_selectors:
            author_element = post_element.select_one(selector)
            if author_element and author_element.get_text(strip=True):
                author = author_element.get_text(strip=True)
                break

        # Find company information - multiple possible selectors
        company = "Unknown"
        company_selectors = [
            "span.feed-shared-actor__description",
            "span.update-components-actor__description",
            "span.feed-shared-actor__sub-description",
            "span.update-components-actor__sub-description",
            ".feed-shared-actor__company-name",
            ".update-components-actor__company-name",
            "a.company-link"
        ]
        
        for selector in company_selectors:
            company_element = post_element.select_one(selector)
            if company_element:
                company_text = company_element.get_text(strip=True)
                # Clean up the company text
                if "•" in company_text:
                    parts = company_text.split("•")
                    if len(parts) > 1:
                        company = parts[0].strip()
                else:
                    company = company_text
                break

        # Get post content with expanded selectors
        content = ""
        content_selectors = [
            "div.feed-shared-update-v2__description",
            "div.update-components-text",
            "div.feed-shared-text",
            "div.feed-shared-update-v2__commentary",
            "span.break-words",
            "div.feed-shared-inline-show-more-text"
        ]
        
        for selector in content_selectors:
            content_element = post_element.select_one(selector)
            if content_element:
                # Get all text elements, including nested spans
                text_elements = content_element.find_all(["span", "p", "div"], class_="break-words")
                if text_elements:
                    content = " ".join(elem.get_text(strip=True) for elem in text_elements)
                else:
                    content = content_element.get_text(strip=True)
                break

        # profile_link = post_element.select_one("a.app-aware-link")
        # if profile_link and 'href' in profile_link.attrs:
        #     profile_url = profile_link['href']
        #     # Extract username from profile URL if available
        #     if '/in/' in profile_url:
        #         username = profile_url.split('/in/')[-1].split('/')[0]

        # Only return if we have meaningful content
        if content.strip() or author != "Unknown" or company != "Unknown":
            post_data = {
                "author": author,
                "company": company,
                "post": content.strip(),
                "profile_url": profile_url,
                "username": username  # Add username to the response
            }
            logger.debug(f"Successfully extracted post: {post_data}")
            return post_data
        return None
    except Exception as e:
        logger.error(f"Error extracting post data: {str(e)}")
        logger.error(f"Post element HTML: {post_element}")
        return None

def search_posts(
    driver: webdriver.Chrome,
    keyword: str,
    limit: int = 10,
    page: int = 1,
    seen_hashes: Set[str] = None
) -> List[Dict]:
    """Scrapes LinkedIn posts with pagination"""
    try:
        if seen_hashes is None:
            seen_hashes = set()
            
        offset = (page - 1) * limit
        search_url = (
            f"https://www.linkedin.com/search/results/content/"
            f"?keywords={keyword.replace(' ', '%20')}"
            f"&origin=GLOBAL_SEARCH_HEADER"
            f"&sortBy=recent"
            f"&start={offset}"
        )
        
        driver.get(search_url)
        time.sleep(3)
        
        posts = []
        scroll_attempts = 0
        max_scrolls = 3
        
        while len(posts) < limit and scroll_attempts < max_scrolls:
            # Get page source after JavaScript rendering
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Updated selectors for post containers
            post_elements = (
                soup.find_all("div", class_="feed-shared-update-v2") or
                soup.find_all("div", class_="relative") or
                soup.find_all("div", class_="occludable-update") or
                soup.find_all("div", attrs={"data-urn": True})
            )
            
            for post_element in post_elements:
                if len(posts) >= limit:
                    break
                    
                post_data = extract_post_data(post_element)
                if post_data:
                    post_hash = get_post_hash(post_data)
                    if post_hash not in seen_hashes:
                        post_data["keyword"] = keyword
                        posts.append(post_data)
                        seen_hashes.add(post_hash)
                        logger.debug(f"Added new post from {post_data['author']}")
            
            if len(posts) < limit:
                # Scroll and wait for new content
                last_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased wait time
                
                # Click "Show more" buttons if present
                try:
                    show_more_buttons = driver.find_elements(By.CSS_SELECTOR, "button.feed-shared-inline-show-more-text__button")
                    for button in show_more_buttons:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                except Exception as e:
                    logger.debug(f"No 'Show more' buttons found: {str(e)}")
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # Reset counter if we loaded new content
                
                last_height = new_height
        
        valid_posts = [p for p in posts if p["author"] != "Unknown" or p["company"] != "Unknown"]
        logger.info(f"Found {len(valid_posts)} valid posts for keyword: {keyword}")
        return valid_posts[:limit]
        
    except Exception as e:
        logger.error(f"Error searching posts for keyword {keyword}: {str(e)}")
        return []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/scrape")
async def scrape_linkedin(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to scrape LinkedIn posts with pagination and caching
    """
    try:
        all_posts = []
        for keyword in request.keywords:
            # Check cache first
            cached_posts = PostCache.get_posts(keyword, request.page)
            if cached_posts:
                all_posts.extend(cached_posts)
                continue
            
            # If not in cache, scrape new posts
            driver = LinkedInDriver.get_instance().get_driver()
            seen_hashes = PostCache.get_seen_hashes(keyword)
            
            posts = search_posts(
                driver=driver,
                keyword=keyword,
                limit=request.limit,
                page=request.page,
                seen_hashes=seen_hashes
            )
            
            # Cache the results
            PostCache.save_posts(keyword, request.page, posts)
            all_posts.extend(posts)
            
            # Update seen hashes
            for post in posts:
                PostCache.add_seen_hash(keyword, get_post_hash(post))
        
        # Schedule background refresh if cache is getting old
        background_tasks.add_task(refresh_cache, request.keywords)
        
        return {
            "status": "success",
            "total_posts": len(all_posts),
            "posts": all_posts,
            "page": request.page
        }
    
    except Exception as e:
        logger.error(f"Error in scraping process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def refresh_cache(keywords: List[str]):
    """Background task to refresh cache"""
    try:
        driver = LinkedInDriver.get_instance().get_driver()
        for keyword in keywords:
            posts = search_posts(driver, keyword, limit=20, page=1)
            PostCache.save_posts(keyword, 1, posts)
    except Exception as e:
        logger.error(f"Cache refresh failed: {str(e)}")

@app.get("/search/{keyword}")
async def search_linkedin_content(keyword: str):
    try:
        scraper = LinkedInPublicScraper()
        results = scraper.search_content(keyword)
        
        return {
            "status": "success",
            "keyword": keyword,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_proxy():
    proxies = [
        'http://proxy1:port',
        'http://proxy2:port'
    ]
    return random.choice(proxies)

class LinkedInPublicScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/learning/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def search_content(self, keyword: str) -> List[Dict]:
        try:
            # Encode the keyword for URL
            encoded_keyword = quote_plus(keyword)
            url = f"{self.base_url}?keywords={encoded_keyword}"
            
            # Add random delay between requests
            time.sleep(random.uniform(3, 7))
            
            # Make the request
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the content
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find all course/video entries
            entries = soup.find_all('div', {'class': 'results-list__item'})
            
            for entry in entries:
                result = {
                    'title': None,
                    'duration': None,
                    'type': None,
                    'author': None,
                    'viewers': None
                }
                
                # Extract title
                title_elem = entry.find('h3')
                if title_elem:
                    result['title'] = title_elem.text.strip()
                
                # Extract duration
                duration_elem = entry.find('span', {'class': 'duration'})
                if duration_elem:
                    result['duration'] = duration_elem.text.strip()
                
                # Extract type (Course/Video)
                type_elem = entry.find('span', {'class': 'type'})
                if type_elem:
                    result['type'] = type_elem.text.strip()
                
                results.append(result)
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing content: {str(e)}")
            return []

# scraper = LinkedInPublicScraper()
# results = scraper.search_content("data lineage")
# print(results)