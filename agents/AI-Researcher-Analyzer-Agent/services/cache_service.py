from redis import Redis
import json
from typing import List, Dict, Optional, Set
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)
# Redis(host=os.getenv("REDIS_HOST"), 
#                     port=6379, 
#                     db=0,
#                     password=os.getenv("REDIS_PASSWORD"),
#                     ssl=True,
#                     decode_responses=True
#                     )
class CacheService:
    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=True,
            decode_responses=True
        )
        logger.info("Redis cache service initialized")

    def get_cache_key(self, keyword: str, page: int) -> str:
        return f"linkedin_posts:{keyword}:{page}"

    def get_posts(self, keyword: str, page: int) -> Optional[List[Dict]]:
        try:
            cache_key = self.get_cache_key(keyword, page)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    def save_posts(self, keyword: str, page: int, posts: List[Dict]):
        try:
            cache_key = self.get_cache_key(keyword, page)
            self.redis_client.setex(
                cache_key,
                settings.CACHE_EXPIRY,
                json.dumps(posts)
            )
            logger.debug(f"Saved posts to cache with key: {cache_key}")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")

    def get_seen_hashes(self, keyword: str) -> Set[str]:
        try:
            seen_key = f"seen_hashes:{keyword}"
            seen_hashes = self.redis_client.smembers(seen_key)
            return seen_hashes if seen_hashes else set()
        except Exception as e:
            logger.error(f"Error retrieving seen hashes: {str(e)}")
            return set()

    def add_seen_hash(self, keyword: str, post_hash: str):
        try:
            seen_key = f"seen_hashes:{keyword}"
            self.redis_client.sadd(seen_key, post_hash)
            self.redis_client.expire(seen_key, settings.CACHE_EXPIRY)
            logger.debug(f"Added hash to seen set: {post_hash}")
        except Exception as e:
            logger.error(f"Error adding seen hash: {str(e)}") 