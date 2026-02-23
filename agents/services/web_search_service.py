import os
import logging
from typing import List, Dict, Optional, Any
from serpapi import GoogleSearch
import asyncio

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.api_key = os.getenv("SERP_API_KEY")
        if not self.api_key:
            logger.warning("SERP_API_KEY not found in environment variables")
        
    async def search_google(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a Google search using SerpAPI.
        """
        if not self.api_key:
            logger.error("Cannot perform search: SERP_API_KEY missing")
            return []

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }

            # Run blocking synchronous code in a thread executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: GoogleSearch(params).get_dict())

            if "error" in results:
                logger.error(f"SerpAPI Error: {results['error']}")
                return []

            organic_results = results.get("organic_results", [])
            processed_results = []

            for result in organic_results:
                processed_results.append({
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "source": "Google"
                })

            return processed_results

        except Exception as e:
            logger.error(f"Error executing Google search for '{query}': {str(e)}")
            return []

    async def search_linkedin_profiles(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Specialized search for LinkedIn profiles via Google.
        """
        # Ensure the query targets LinkedIn profiles if not already
        if "site:linkedin.com/in/" not in query:
            query = f"site:linkedin.com/in/ {query}"
        
        results = await self.search_google(query, num_results)
        
        # Post-process to ensure we only get LinkedIn profile links
        linkedin_results = []
        for result in results:
            if "linkedin.com/in/" in result.get("link", ""):
                result["source"] = "LinkedIn"
                linkedin_results.append(result)
        
        return linkedin_results

    async def search_reddit(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search Reddit content via Google.
        """
        if "site:reddit.com" not in query:
            query = f"site:reddit.com {query}"
            
        results = await self.search_google(query, num_results)
        
        for result in results:
            result["source"] = "Reddit"
            
        return results
