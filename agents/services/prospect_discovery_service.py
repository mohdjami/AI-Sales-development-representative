import logging
from typing import List, Dict, Any
from googlesearch import search
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ProspectDiscoveryService:
    def __init__(self):
        self.llm_service = LLMService()

    async def discover_prospects(self, company_description: str, goal: str, job_titles: List[str]) -> List[Dict[str, Any]]:
        """
        Discover prospects using Google Search and Reddit based on user preferences.
        """
        all_prospects = []
        
        # 1. Generate optimized search queries using LLM
        search_queries = await self._generate_search_queries(company_description, goal, job_titles)
        logger.info(f"Generated search queries: {search_queries}")
        
        # 2. Execute searches with rate limiting
        import time
        import random

        for query in search_queries:
            logger.info(f"Searching Google for: {query}")
            try:
                # Add random delay to avoid 429
                time.sleep(random.uniform(2, 5))
                
                results = search(query, num_results=4, advanced=True)
                results_list = list(results)
                logger.info(f"Found {len(results_list)} results for query: {query}")
                
                for result in results_list:
                     all_prospects.append({
                        "source": "Google/LinkedIn" if "linkedin.com" in result.url else "Google/Web",
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.description,
                        "search_term": query
                    })
            except Exception as e:
                logger.error(f"Error searching Google for {query}: {str(e)}")

        # 3. Analyze and Score Prospects using LLM
        # Remove duplicates based on URL
        unique_prospects = {p['url']: p for p in all_prospects}.values()
        
        analyzed_prospects = await self._analyze_prospects(list(unique_prospects), company_description, goal)
        return analyzed_prospects


    async def _generate_search_queries(self, company_desc: str, goal: str, job_titles: List[str]) -> List[str]:
        """Generate effective Google search queries."""
        system_prompt = "You are an expert at creating Google search queries to find professional prospects."
        user_prompt = f"""
        I need to find prospects for my company.
        My Company: {company_desc}
        My Goal: {goal}
        Target Job Titles: {', '.join(job_titles)}

        Generate 3-5 specific Google search queries to find these people on LinkedIn or other professional sites.
        Use "site:linkedin.com/in/" for at least half of the queries.
        Focus on finding profiles that match the goal (e.g. "B2B SaaS", "Marketing", etc).
        
        Return ONLY a JSON list of strings.
        Example: ["site:linkedin.com/in/ 'Head of Sales' 'B2B SaaS'", "site:linkedin.com/in/ 'SDR Manager' 'Technology'"]
        """
        
        json_structure = {"queries": ["string"]}

        try:
            response = await self.llm_service.get_json_response(
                system_prompt=system_prompt, 
                user_prompt=user_prompt,
                json_structure=json_structure
            )
            
            if isinstance(response, dict) and "queries" in response:
                return response["queries"]
            else:
                 # Fallback
                 return [f'site:linkedin.com/in/ "{t}"' for t in job_titles]
        except Exception as e:
            logger.error(f"Error generating queries: {str(e)}")
            return [f'site:linkedin.com/in/ "{t}"' for t in job_titles]

    async def _analyze_prospects(self, raw_prospects: List[Dict], company_desc: str, goal: str) -> List[Dict]:
        """
        Filter and score prospects using LLM.
        """
        if not raw_prospects:
            return []

        system_prompt = """You are an expert SDR agent. 
        Your goal is to analyze search results (LinkedIn profiles or Reddit threads) and determine if they represent good prospects based on the user's company and goal.
        Return a JSON object with a list of analyzed prospects.
        """
        
        # Prepare content for LLM
        prospects_str = ""
        for i, p in enumerate(raw_prospects):
            prospects_str += f"[{i}] Title: {p['title']}\nSnippet: {p['snippet']}\nURL: {p['url']}\nSource: {p['source']}\n\n"

        user_prompt = f"""
        My Company: {company_desc}
        My Goal: {goal}

        Analyze these search results and identify potential prospects:
        {prospects_str}

        For each prospect, provide:
        - name (extract from title if possible, or "Unknown")
        - role (extract from title/snippet)
        - company (extract from title/snippet)
        - alignment_score (0.0 to 1.0)
        - reason (why they are a good fit)
        - is_prospect (boolean)

        Return format:
        {{
            "prospects": [
                {{
                    "original_index": 0,
                    "name": "...",
                    "role": "...",
                    "company": "...",
                    "alignment_score": 0.8,
                    "reason": "...",
                    "is_prospect": true
                }}
            ]
        }}
        """

        try:
            # We assume LLMService has a method to get JSON response
            # Note: You might need to adjust LLMService usage based on its actual implementation
            response = await self.llm_service.get_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            final_list = []
            if "prospects" in response:
                for item in response["prospects"]:
                    if item.get("is_prospect"):
                        idx = item.get("original_index")
                        if idx is not None and 0 <= idx < len(raw_prospects):
                            original = raw_prospects[idx]
                            final_list.append({
                                **item,
                                "url": original["url"],
                                "source": original["source"]
                            })
            
            return sorted(final_list, key=lambda x: x['alignment_score'], reverse=True)

        except Exception as e:
            logger.error(f"Error analyzing prospects with LLM: {str(e)}")
            return []
