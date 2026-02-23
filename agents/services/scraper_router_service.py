"""
AI Scraper Router Service
=========================
Uses an LLM to intelligently decide which scrapers to run based on
the user's prospect search goal, saving time and avoiding irrelevant sources.

Flow:
  1. Receive: goal, company_description, job_titles, optional keyword hints
  2. LLM call → produces { selected_scrapers: [...], params: {...}, rationale: "..." }
  3. Map scraper names to PlaywrightScraperService methods + runtime params
  4. Execute selected scrapers in parallel via PlaywrightScraperService.run_scrapers()
  5. Return merged, deduplicated results
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from services.llm_service import LLMService
from services.playwright_scraper_service import PlaywrightScraperService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scraper capability registry — LLM uses this to decide which scrapers to use
# ---------------------------------------------------------------------------
SCRAPER_REGISTRY = {
    "product_hunt": {
        "description": "Finds new product founders/makers on Product Hunt. Best for: B2B SaaS, dev tools, early-stage startups.",
        "required_params": ["keyword"],
        "optional_params": ["limit"],
    },
    "g2": {
        "description": "Finds dissatisfied users of competitor products on G2 reviews. Best for: product-led sales, replacing incumbents.",
        "required_params": ["competitor_slug"],
        "optional_params": ["sentiment", "limit"],
    },
    "hacker_news": {
        "description": "Scrapes HN 'Who is Hiring' thread for companies and roles. Best for: developer tools, infrastructure, API-first products.",
        "required_params": ["keyword"],
        "optional_params": ["limit"],
    },
    "github": {
        "description": "Finds public members/contributors of GitHub organizations. Best for: selling to open-source companies, dev tools, infra.",
        "required_params": ["org_name"],
        "optional_params": ["limit"],
    },
    "crunchbase": {
        "description": "Finds founders and executives by industry on Crunchbase. Best for: B2B sales targeting funded startups, funding signal-driven outreach.",
        "required_params": ["keyword"],
        "optional_params": ["funding_stage", "limit"],
    },
    "wellfound": {
        "description": "Finds startup employees and decision-makers on Wellfound (AngelList Talent). Best for: Series A-B companies scaling teams.",
        "required_params": ["role"],
        "optional_params": ["keyword", "limit"],
    },
    "yc_directory": {
        "description": "Finds YC-backed company founders filtered by topic/industry. Best for: selling to high-growth, well-funded, founder-led startups.",
        "required_params": ["keyword"],
        "optional_params": ["batch", "limit"],
    },
    "angellist": {
        "description": "Finds investors and founders by market on AngelList. Best for: VC-backed company outreach, investor-led introductions.",
        "required_params": ["market"],
        "optional_params": ["role", "limit"],
    },
}


class ScraperRouterService:
    """
    AI-driven router that selects and configures the best scrapers
    for a given prospect discovery goal.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.playwright_service = PlaywrightScraperService()

    async def route_and_scrape(
        self,
        goal: str,
        company_description: str,
        job_titles: List[str],
        keyword_hint: str = "",
        max_scrapers: int = 3,
        max_results_per_scraper: int = 8,
    ) -> Dict[str, Any]:
        """
        Main entry point: AI picks scrapers, runs them, returns merged results.

        Returns:
            {
              "prospects": [...],
              "scrapers_used": [...],
              "rationale": "...",
            }
        """
        # Step 1: AI picks scrapers
        routing = await self._ai_pick_scrapers(
            goal=goal,
            company_description=company_description,
            job_titles=job_titles,
            keyword_hint=keyword_hint,
            max_scrapers=max_scrapers,
            max_results_per_scraper=max_results_per_scraper,
        )

        selected_scrapers = routing.get("selected_scrapers", [])
        scraper_params    = routing.get("params", {})
        rationale         = routing.get("rationale", "")

        logger.info(f"[Router] AI selected scrapers: {selected_scrapers}")
        logger.info(f"[Router] Rationale: {rationale}")

        if not selected_scrapers:
            logger.warning("[Router] AI returned no scrapers — using defaults")
            selected_scrapers = ["product_hunt", "wellfound"]
            scraper_params = {
                "product_hunt": {"keyword": keyword_hint or goal[:50]},
                "wellfound": {"role": job_titles[0] if job_titles else "founder"},
            }

        # Step 2: Build scraper call specs
        scraper_calls = self._build_scraper_calls(
            selected_scrapers, scraper_params, max_results_per_scraper
        )

        # Step 3: Run scrapers in parallel
        prospects = await self.playwright_service.run_scrapers(scraper_calls)

        return {
            "prospects": prospects,
            "scrapers_used": selected_scrapers,
            "rationale": rationale,
        }

    async def _ai_pick_scrapers(
        self,
        goal: str,
        company_description: str,
        job_titles: List[str],
        keyword_hint: str,
        max_scrapers: int,
        max_results_per_scraper: int,
    ) -> Dict[str, Any]:
        """Call LLM to select the best scrapers and build their parameters."""

        registry_desc = "\n".join(
            f'- "{name}": {info["description"]} Required params: {info["required_params"]}. Optional: {info["optional_params"]}.'
            for name, info in SCRAPER_REGISTRY.items()
        )

        system_prompt = """You are an AI sales development assistant expert at lead generation strategy.
Your job is to select the BEST web scrapers for a given prospect search goal and configure their parameters.
Be precise and practical. Only pick scrapers that are highly relevant to the stated goal.
Always return valid JSON."""

        user_prompt = f"""## Prospect Search Goal
**Company Description:** {company_description}
**Goal:** {goal}
**Target Job Titles:** {", ".join(job_titles) if job_titles else "Not specified"}
**Keyword Hint:** {keyword_hint or "None"}

## Available Scrapers
{registry_desc}

## Instructions
1. Select the {max_scrapers} MOST suitable scrapers from the list above
2. For each selected scraper, provide the EXACT parameters it needs (see required_params)
3. Parameters must be relevant strings (e.g., competitor_slug for G2 should be a real product name like "salesforce" or "hubspot")
4. Think step by step: which sources would actually have these prospects?

## Required JSON Output Format
{{
  "selected_scrapers": ["scraper_name_1", "scraper_name_2"],
  "params": {{
    "scraper_name_1": {{ "keyword": "...", "limit": {max_results_per_scraper} }},
    "scraper_name_2": {{ "role": "...", "limit": {max_results_per_scraper} }}
  }},
  "rationale": "One sentence explaining why these sources are best for this goal"
}}"""

        structure = {
            "selected_scrapers": ["string"],
            "params": {},
            "rationale": "string",
        }

        try:
            result = await self.llm_service.get_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_structure=structure,
            )
            # Validate
            if not isinstance(result.get("selected_scrapers"), list):
                raise ValueError("selected_scrapers must be a list")
            # Filter to valid scraper names only
            valid = [s for s in result["selected_scrapers"] if s in SCRAPER_REGISTRY]
            result["selected_scrapers"] = valid[:max_scrapers]
            return result
        except Exception as e:
            logger.error(f"[Router] LLM routing failed: {e}")
            return {}

    def _build_scraper_calls(
        self,
        selected_scrapers: List[str],
        params: Dict[str, Dict],
        limit: int,
    ) -> List[Dict]:
        """Convert routing decision into the call spec format for run_scrapers()."""
        calls = []
        for scraper_name in selected_scrapers:
            info = SCRAPER_REGISTRY.get(scraper_name)
            if not info:
                continue

            # Start with AI-provided params; ensure limit is set
            kwargs = dict(params.get(scraper_name, {}))
            kwargs["limit"] = kwargs.get("limit", limit)

            # Validate required params exist; skip scraper if missing
            missing = [p for p in info["required_params"] if p not in kwargs]
            if missing:
                logger.warning(
                    f"[Router] Skipping '{scraper_name}' — missing required params: {missing}"
                )
                continue

            calls.append({"scraper": scraper_name, "kwargs": kwargs})

        return calls

    async def close(self):
        await self.playwright_service.close()
