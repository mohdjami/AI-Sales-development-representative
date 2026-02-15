from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import hashlib
import time

from services.driver_service import LinkedInDriver
from services.cache_service import CacheService
from config.settings import settings
from utils.logger import setup_logger
from models.schemas import Post

logger = setup_logger(__name__)

class ScraperService:
    def __init__(self):
        self.driver_service = LinkedInDriver.get_instance()
        self.cache_service = CacheService()
        logger.info("Scraper service initialized")

    def get_post_hash(self, post: Dict) -> str:
        """Generate a unique hash for a post to prevent duplicates"""
        content = f"{post['author']}{post['company']}{post['post']}"
        return hashlib.md5(content.encode()).hexdigest()

    async def extract_post_data(self, post_element) -> Optional[Post]:
        """Extract structured data from a post element"""
        try:
            logger.debug("Extracting data from post element")
            
            # Initialize post data
            post_data = {
                "author": "Unknown",
                "role": "Unknown",
                "company": "Unknown",
                "post": "",
                "profile_url": "",
                "username": ""
            }

            # Extract author information
            author_element = post_element.select_one("span.feed-shared-actor__title")
            if author_element:
                post_data["author"] = author_element.get_text(strip=True)

            # Extract role
            role_element = post_element.select_one("span.feed-shared-actor__description")
            if role_element:
                post_data["role"] = role_element.get_text(strip=True)

            # Extract company
            company_element = post_element.select_one("span.feed-shared-actor__sub-description")
            if company_element:
                post_data["company"] = company_element.get_text(strip=True)

            # Extract post content
            content_element = post_element.select_one("div.feed-shared-update-v2__description")
            if content_element:
                post_data["post"] = content_element.get_text(strip=True)

            # Extract profile URL and username
            profile_link = post_element.select_one("a.app-aware-link[href*='/in/']")
            if profile_link and 'href' in profile_link.attrs:
                post_data["profile_url"] = profile_link['href']
                username = profile_link['href'].split('/in/')[-1].split('?')[0]
                post_data["username"] = username

            return Post(**post_data)

        except Exception as e:
            logger.error(f"Error extracting post data: {str(e)}")
            return None

    async def search_posts(self, keywords: List[str], page: int = 1, limit: int = 10) -> List[Post]:
        """Search LinkedIn posts for given keywords"""
        all_posts = []
        driver = self.driver_service.get_driver()

        for keyword in keywords:
            try:
                # Check cache first
                cached_posts = self.cache_service.get_posts(keyword, page)
                if cached_posts:
                    logger.info(f"Retrieved cached posts for keyword: {keyword}")
                    all_posts.extend(cached_posts)
                    continue

                # Search for posts
                search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&origin=GLOBAL_SEARCH_HEADER"
                driver.get(search_url)
                
                # Wait for posts to load and scroll
                time.sleep(settings.SCROLL_PAUSE_TIME)
                
                # Scroll to load more posts
                for _ in range(settings.MAX_SCROLL_ATTEMPTS):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(settings.SCROLL_PAUSE_TIME)

                # Parse the page
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                post_elements = soup.select("div.feed-shared-update-v2")

                keyword_posts = []
                for post_element in post_elements[:limit]:
                    post = await self.extract_post_data(post_element)
                    if post:
                        post.keyword = keyword
                        post_hash = self.get_post_hash(post.dict())
                        
                        # Check if we've seen this post before
                        if post_hash not in self.cache_service.get_seen_hashes(keyword):
                            keyword_posts.append(post)
                            self.cache_service.add_seen_hash(keyword, post_hash)

                # Cache the results
                self.cache_service.save_posts(keyword, page, [post.dict() for post in keyword_posts])
                all_posts.extend(keyword_posts)

            except Exception as e:
                logger.error(f"Error searching posts for keyword {keyword}: {str(e)}")
                continue

        return all_posts[:limit] 