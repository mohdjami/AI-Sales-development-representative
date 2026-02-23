import os
import logging
import praw
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RedditService:
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "python:ai-sdr-agent:v1.0 (by /u/your_username)")
        
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not found. Reddit search will be disabled.")
            self.reddit = None
        else:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("Reddit API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit API: {str(e)}")
                self.reddit = None

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for Reddit posts.
        """
        if not self.reddit:
            logger.warning("Reddit API not initialized. Skipping Reddit search.")
            return []

        try:
            # PRAW search is synchronous, so we should run it in an executor if strict async is needed,
            # but for simplicity in this MVP we'll run it directly or wrap if it blocks too long.
            # Convert async call pattern if needed, but PRAW is sync.
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _search():
                subreddit = self.reddit.subreddit("all")
                results = []
                # search() returns a generator
                for submission in subreddit.search(query, limit=limit):
                    results.append({
                        "title": submission.title,
                        "url": submission.url,
                        "snippet": submission.selftext[:300] if submission.selftext else submission.title,
                        "source": "Reddit",
                        "author": str(submission.author),
                        "subreddit": str(submission.subreddit),
                        "score": submission.score,
                        "created_utc": submission.created_utc
                    })
                return results

            results = await loop.run_in_executor(None, _search)
            return results

        except Exception as e:
            logger.error(f"Error searching Reddit for '{query}': {str(e)}")
            return []
