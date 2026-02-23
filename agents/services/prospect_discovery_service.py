"""
Prospect Discovery Service (Enhanced)
======================================
Multi-source prospect discovery pipeline:
  1. LLM generates optimized search queries
  2. Google Search + Reddit (existing)
  3. AI-routed Playwright scrapers: Product Hunt, G2, HN, GitHub,
     Crunchbase, Wellfound, YC Directory, AngelList (NEW)
  4. LLM analyzes + scores all prospects
  5. Email discovery + verification for top prospects (NEW)
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional

from services.llm_service import LLMService
from services.web_search_service import WebSearchService
from services.query_generator_service import QueryGeneratorService
from services.scraper_router_service import ScraperRouterService
from services.email_discovery_service import EmailDiscoveryService

logger = logging.getLogger(__name__)


class ProspectDiscoveryService:
    def __init__(self):
        self.llm_service = LLMService()
        self.web_search_service = WebSearchService()
        self.query_generator_service = QueryGeneratorService()
        self.scraper_router = ScraperRouterService()
        self.email_discovery = EmailDiscoveryService()

    async def discover_prospects(
        self,
        company_description: str,
        goal: str,
        job_titles: List[str],
        enable_playwright: bool = True,
        enable_email_discovery: bool = True,
        keyword_hint: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Discover prospects using multiple parallel sources:
          - Google Search (existing)
          - Reddit (existing)
          - AI-selected Playwright scrapers (new)
        Then score, enrich with emails, and return.
        """
        preferences = {
            "company_description": company_description,
            "goal": goal,
            "target_job_titles": job_titles,
            "target_industries": [],
            "target_locations": [],
        }

        # ── Source 1 & 2: Google + Reddit (existing flow) ──────────────────
        google_reddit_task = self._run_google_reddit_search(preferences, goal, job_titles)

        # ── Source 3: AI-routed Playwright scrapers (new) ──────────────────
        if enable_playwright:
            playwright_task = self.scraper_router.route_and_scrape(
                goal=goal,
                company_description=company_description,
                job_titles=job_titles,
                keyword_hint=keyword_hint,
                max_scrapers=3,
                max_results_per_scraper=8,
            )
        else:
            async def _no_playwright():
                return {"prospects": []}
            playwright_task = _no_playwright()


        # Run both in parallel
        google_reddit_results, playwright_result = await asyncio.gather(
            google_reddit_task,
            playwright_task,
            return_exceptions=True,
        )

        # Merge all raw results
        all_raw = []
        if isinstance(google_reddit_results, list):
            all_raw.extend(google_reddit_results)
        else:
            logger.error(f"Google/Reddit search failed: {google_reddit_results}")

        if isinstance(playwright_result, dict):
            pw_prospects = playwright_result.get("prospects", [])
            logger.info(
                f"[Playwright] Added {len(pw_prospects)} results "
                f"(scrapers: {playwright_result.get('scrapers_used', [])}). "
                f"Rationale: {playwright_result.get('rationale', '')}"
            )
            # Adapt playwright results to match web search result format
            for p in pw_prospects:
                all_raw.append({
                    "source":      p.get("source", "Web Scraper"),
                    "title":       f"{p.get('name', '')} — {p.get('role', '')} at {p.get('company', '')}",
                    "url":         p.get("url", ""),
                    "snippet":     p.get("snippet", ""),
                    "search_term": goal,
                    # Carry over structured fields for LLM context
                    "_name":       p.get("name", ""),
                    "_role":       p.get("role", ""),
                    "_company":    p.get("company", ""),
                    "_email":      p.get("email"),
                })
        elif isinstance(playwright_result, Exception):
            logger.error(f"Playwright scraping failed: {playwright_result}")

        # ── Dedup by URL ───────────────────────────────────────────────────
        unique_map: Dict[str, Dict] = {}
        for p in all_raw:
            key = p.get("url") or p.get("title", "")
            if key and key not in unique_map:
                unique_map[key] = p

        unique_list = list(unique_map.values())
        logger.info(f"[Discovery] {len(unique_list)} unique prospects from all sources before LLM analysis")

        # ── LLM Analysis & Scoring ─────────────────────────────────────────
        analyzed = await self._analyze_prospects(unique_list, company_description, goal)

        # ── Email Enrichment (top prospects only) ──────────────────────────
        if enable_email_discovery and analyzed:
            analyzed = await self._enrich_with_emails(analyzed)

        return analyzed

    # ──────────────────────────────────────────────────────────────────────
    # Private: Google + Reddit search (unchanged from original)
    # ──────────────────────────────────────────────────────────────────────
    async def _run_google_reddit_search(
        self, preferences: Dict, goal: str, job_titles: List[str]
    ) -> List[Dict]:
        import random, time

        all_prospects = []
        try:
            search_queries = await self.query_generator_service.generate_search_queries(preferences)
            logger.info(f"Generated search queries: {search_queries}")
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return []

        for query in search_queries:
            logger.info(f"Searching Google for: {query}")
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                if "site:linkedin.com/in/" in query:
                    results = await self.web_search_service.search_linkedin_profiles(query, num_results=5)
                elif "site:reddit.com" in query:
                    results = await self.web_search_service.search_reddit(query, num_results=5)
                else:
                    results = await self.web_search_service.search_google(query, num_results=5)

                logger.info(f"Found {len(results)} results for: {query}")
                for result in results:
                    all_prospects.append({
                        "source":      result.get("source", "Web"),
                        "title":       result.get("title"),
                        "url":         result.get("link"),
                        "snippet":     result.get("snippet"),
                        "search_term": query,
                    })
            except Exception as e:
                logger.error(f"Error searching '{query}': {e}")

        return all_prospects

    # ──────────────────────────────────────────────────────────────────────
    # Private: LLM analysis (enhanced to use structured playwright fields)
    # ──────────────────────────────────────────────────────────────────────
    async def _analyze_prospects(
        self, raw_prospects: List[Dict], company_desc: str, goal: str
    ) -> List[Dict]:
        if not raw_prospects:
            return []

        system_prompt = """You are an expert SDR agent.
Your goal is to analyze search results and scraped prospect data to identify
high-quality leads based on the user's company and goal.
Use any structured fields (_name, _role, _company) when available.
Return a JSON list of analyzed prospects."""

        candidates = raw_prospects[:20] if len(raw_prospects) > 20 else raw_prospects

        user_prompt = f"""
**My Company:** {company_desc}
**My Goal:** {goal}

**Candidates to Analyze:**
{json.dumps(candidates, indent=2)}

**Output Format (JSON List):**
[
  {{
    "name": "Full Name",
    "role": "Job Title",
    "company": "Company Name",
    "email": "email@example.com or null",
    "industry": "Industry (e.g. SaaS, Healthcare)",
    "source": "LinkedIn / Product Hunt / G2 / etc.",
    "url": "profile or source URL",
    "pain_points": ["Point 1", "Point 2"],
    "solution_fit": "1-sentence explanation of fit",
    "insights": "1-sentence personalized insight",
    "alignment_score": 0.95,
    "is_prospect": true
  }}
]
"""
        structure = [
            {
                "name": "string",
                "role": "string",
                "company": "string",
                "email": "string",
                "industry": "string",
                "source": "string",
                "url": "string",
                "pain_points": ["string"],
                "solution_fit": "string",
                "insights": "string",
                "alignment_score": 0.0,
                "is_prospect": True,
            }
        ]

        try:
            analyzed_data = await self.llm_service.get_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_structure=structure,
            )

            final_list = []
            if isinstance(analyzed_data, list):
                for p in analyzed_data:
                    if p.get("name") == "Unknown" and p.get("company") == "Unknown":
                        continue
                    p["alignment_score"] = float(p.get("alignment_score", 0))
                    if not isinstance(p.get("pain_points"), list):
                        p["pain_points"] = []
                    final_list.append(p)

            return sorted(final_list, key=lambda x: x.get("alignment_score", 0), reverse=True)

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────
    # Private: Email enrichment for high-score prospects
    # ──────────────────────────────────────────────────────────────────────
    async def _enrich_with_emails(
        self, prospects: List[Dict], min_score: float = 0.6, max_to_enrich: int = 10
    ) -> List[Dict]:
        """
        For top prospects (alignment_score ≥ min_score), attempt to
        discover and verify their email address.
        Runs enrichment tasks in parallel (up to max_to_enrich).
        """
        to_enrich = [
            p for p in prospects
            if p.get("alignment_score", 0) >= min_score and not p.get("email")
        ][:max_to_enrich]

        if not to_enrich:
            logger.info("[Email] No prospects need email enrichment")
            return prospects

        logger.info(f"[Email] Enriching {len(to_enrich)} top prospects with email discovery")

        tasks = [
            self.email_discovery.enrich_prospect_email(p)
            for p in to_enrich
        ]
        enriched = await asyncio.gather(*tasks, return_exceptions=True)

        # Build lookup map: name+company → enriched data
        enrichment_map: Dict[str, Dict] = {}
        for original, result in zip(to_enrich, enriched):
            if isinstance(result, Exception):
                logger.warning(f"[Email] Enrichment failed for {original.get('name')}: {result}")
                continue
            key = f"{original.get('name','')}|{original.get('company','')}".lower()
            enrichment_map[key] = result

        # Merge enrichment back into prospects list
        for p in prospects:
            key = f"{p.get('name','')}|{p.get('company','')}".lower()
            if key in enrichment_map:
                enriched_p = enrichment_map[key]
                p["email"]             = enriched_p.get("email") or p.get("email")
                p["email_confidence"]  = enriched_p.get("email_confidence", "unverifiable")
                p["email_candidates"]  = enriched_p.get("email_candidates", [])

        logger.info("[Email] Enrichment complete")
        return prospects
