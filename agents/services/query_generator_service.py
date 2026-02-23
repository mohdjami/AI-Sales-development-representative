import logging
from typing import List, Dict, Any
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class QueryGeneratorService:
    def __init__(self):
        self.llm_service = LLMService()

    async def generate_search_queries(self, preferences: Dict[str, Any]) -> List[str]:
        """
        Generate optimized Google search queries based on user preferences.
        """
        company_description = preferences.get("company_description", "")
        goal = preferences.get("goal", "")
        job_titles = preferences.get("target_job_titles", [])
        industries = preferences.get("target_industries", [])
        locations = preferences.get("target_locations", [])
        
        system_prompt = "You are an expert at creating Google search queries to find professional prospects."
        user_prompt = f"""
        Generate 5 diverse Google search operators to find prospects matching these criteria:
        
        Context:
        - Company: {company_description}
        - Goal: {goal}
        - Target Roles: {', '.join(job_titles)}
        - Industries: {', '.join(industries)}
        - Locations: {', '.join(locations)}

        Strategies to use:
        1. Site search (site:linkedin.com/in/) for direct profile lookup
        2. Boolean logic ("AND", "OR") to combine roles and industries
        3. Exclusion operators (-) to filter irrelevant results if needed
        4. Location based queries if locations are provided
        
        Return ONLY a JSON object with a "queries" key containing a list of strings.
        Example: {{"queries": ["site:linkedin.com/in/ 'Marketing Director' 'SaaS'", "site:linkedin.com/in/ 'CMO' 'Technology'"]}}
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
            return []
            
        except Exception as e:
            logger.error(f"Error generating search queries: {str(e)}")
            # Fallback queries
            return [f"site:linkedin.com/in/ \"{title}\"" for title in job_titles]
