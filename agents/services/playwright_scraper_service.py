"""
Playwright Scraper Service
==========================
8 scrapers for finding B2B prospects across key platforms.
Each scraper returns a normalized List[Dict] with:
  name, role, company, url, source, snippet, email (str|None)

AI Router (ScraperRouterService) picks the best scrapers based on the
user's goal using an LLM call, then runs them in parallel.
"""

import asyncio
import logging
import random
import re
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stealth helpers
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--disable-dev-shm-usage",
    "--window-size=1280,800",
]

def _normalized(
    name: str = "",
    role: str = "",
    company: str = "",
    url: str = "",
    source: str = "",
    snippet: str = "",
    email: Optional[str] = None,
    extra: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Return a normalized prospect dict."""
    result = {
        "name": name.strip(),
        "role": role.strip(),
        "company": company.strip(),
        "url": url.strip(),
        "source": source,
        "snippet": snippet.strip()[:400],
        "email": email,
    }
    if extra:
        result.update(extra)
    return result


async def _delay(min_s: float = 1.5, max_s: float = 4.0):
    await asyncio.sleep(random.uniform(min_s, max_s))


# ---------------------------------------------------------------------------
# PlaywrightScraperService
# ---------------------------------------------------------------------------

class PlaywrightScraperService:
    """
    Manages a single shared browser instance and exposes async scraper
    methods for 8 prospect-discovery platforms.
    """

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def _get_browser(self) -> Browser:
        if self._browser and self._browser.is_connected():
            return self._browser
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=STEALTH_ARGS,
        )
        return self._browser

    async def _new_context(self) -> BrowserContext:
        browser = await self._get_browser()
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        # Mask automation fingerprint
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            window.chrome = { runtime: {} };
        """)
        return ctx

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # ------------------------------------------------------------------ #
    # 1. Product Hunt                                                       #
    # ------------------------------------------------------------------ #
    async def scrape_product_hunt(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Scrapes producthunt.com search results for `keyword`.
        Returns makers/founders of matching products as prospects.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://www.producthunt.com/search?q={keyword.replace(' ', '+')}"
            logger.info(f"[ProductHunt] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await _delay()

            cards = await page.query_selector_all("[data-test='post-item']")
            if not cards:
                # fallback selector
                cards = await page.query_selector_all("article")

            for card in cards[:limit]:
                try:
                    name_el   = await card.query_selector("h3, h2")
                    tagline_el = await card.query_selector("p")
                    link_el   = await card.query_selector("a")
                    name_text   = (await name_el.inner_text()).strip()   if name_el   else ""
                    tagline_txt = (await tagline_el.inner_text()).strip() if tagline_el else ""
                    href        = await link_el.get_attribute("href")    if link_el   else ""
                    full_url    = f"https://www.producthunt.com{href}" if href and href.startswith("/") else href

                    results.append(_normalized(
                        name=name_text,
                        role="Founder / Maker",
                        company=name_text,
                        url=full_url or url,
                        source="Product Hunt",
                        snippet=tagline_txt,
                    ))
                except Exception as e:
                    logger.debug(f"[ProductHunt] card parse error: {e}")
        except Exception as e:
            logger.error(f"[ProductHunt] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[ProductHunt] Found {len(results)} results for '{keyword}'")
        return results

    # ------------------------------------------------------------------ #
    # 2. G2 Reviews                                                         #
    # ------------------------------------------------------------------ #
    async def scrape_g2_reviews(
        self, competitor_slug: str, sentiment: str = "negative", limit: int = 10
    ) -> List[Dict]:
        """
        Scrapes G2 reviews for `competitor_slug`.
        Reviewers who give 1–3 stars are warm prospects (actively dissatisfied).
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://www.g2.com/products/{competitor_slug}/reviews"
            logger.info(f"[G2] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await _delay(2, 5)

            review_cards = await page.query_selector_all("[itemprop='review']")
            if not review_cards:
                review_cards = await page.query_selector_all(".paper.paper--white.paper--box")

            for card in review_cards[:limit]:
                try:
                    reviewer_el = await card.query_selector("[itemprop='author']")
                    title_el    = await card.query_selector("[itemprop='name']")
                    body_el     = await card.query_selector("[itemprop='reviewBody']")
                    job_el      = await card.query_selector(".mt-4th")

                    reviewer = (await reviewer_el.inner_text()).strip() if reviewer_el else "Unknown"
                    title    = (await title_el.inner_text()).strip()    if title_el    else ""
                    body     = (await body_el.inner_text()).strip()[:300] if body_el   else ""
                    job_info = (await job_el.inner_text()).strip()      if job_el      else ""

                    # Parse "Title at Company"
                    role, company = "", ""
                    if " at " in job_info:
                        parts = job_info.split(" at ", 1)
                        role = parts[0].strip()
                        company = parts[1].strip()

                    results.append(_normalized(
                        name=reviewer,
                        role=role,
                        company=company,
                        url=url,
                        source="G2",
                        snippet=f"Review of {competitor_slug}: {body}",
                        extra={"review_title": title},
                    ))
                except Exception as e:
                    logger.debug(f"[G2] card parse error: {e}")
        except Exception as e:
            logger.error(f"[G2] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[G2] Found {len(results)} reviewers for '{competitor_slug}'")
        return results

    # ------------------------------------------------------------------ #
    # 3. Hacker News — "Who is Hiring"                                      #
    # ------------------------------------------------------------------ #
    async def scrape_hacker_news_hiring(self, keyword: str, limit: int = 15) -> List[Dict]:
        """
        Scrapes the latest HN "Who is Hiring" thread (monthly, posted by whoishiring).
        Filters comments matching `keyword`.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            # Search HN for the latest hiring thread
            search_url = f"https://hn.algolia.com/api/v1/search?query=Who+is+Hiring&tags=story,author_whoishiring&hitsPerPage=1"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            content = await page.content()

            # Extract thread ID from JSON response
            thread_id_match = re.search(r'"objectID":"(\d+)"', content)
            if not thread_id_match:
                logger.warning("[HN] Could not find hiring thread ID")
                await ctx.close()
                return results

            thread_id = thread_id_match.group(1)
            thread_url = f"https://news.ycombinator.com/item?id={thread_id}"
            logger.info(f"[HN] Loading thread {thread_url}")

            await page.goto(thread_url, wait_until="domcontentloaded", timeout=25000)
            await _delay(2, 4)

            comments = await page.query_selector_all(".comment-tree .athing.comtr")
            kw_lower = keyword.lower()

            for comment in comments:
                if len(results) >= limit:
                    break
                try:
                    text_el = await comment.query_selector(".comment .commtext")
                    if not text_el:
                        continue
                    text = (await text_el.inner_text()).strip()
                    if kw_lower not in text.lower():
                        continue

                    # First line is usually "Company | Role | Location | Remote/Onsite"
                    lines  = [l.strip() for l in text.split("\n") if l.strip()]
                    first  = lines[0] if lines else ""
                    parts  = [p.strip() for p in first.split("|")]
                    company = parts[0] if parts else ""
                    role    = parts[1] if len(parts) > 1 else keyword
                    snippet = " ".join(lines[:3])

                    user_el  = await comment.query_selector(".hnuser")
                    username = (await user_el.inner_text()).strip() if user_el else ""

                    results.append(_normalized(
                        name=username,
                        role=role,
                        company=company,
                        url=thread_url,
                        source="Hacker News Hiring",
                        snippet=snippet,
                    ))
                except Exception as e:
                    logger.debug(f"[HN] comment parse error: {e}")
        except Exception as e:
            logger.error(f"[HN] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[HN] Found {len(results)} hiring posts for '{keyword}'")
        return results

    # ------------------------------------------------------------------ #
    # 4. GitHub Org                                                          #
    # ------------------------------------------------------------------ #
    async def scrape_github_org(self, org_name: str, limit: int = 10) -> List[Dict]:
        """
        Scrapes github.com/{org_name}/people for public members.
        Returns member names, roles (bio), and profile URLs.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://github.com/orgs/{org_name}/people"
            logger.info(f"[GitHub] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await _delay()

            members = await page.query_selector_all("[data-bulk-actions-id]")
            if not members:
                # Try public members page
                members = await page.query_selector_all(".member-container, li.d-flex")

            for m in members[:limit]:
                try:
                    name_el  = await m.query_selector("a.d-block, span[data-login]")
                    login_el = await m.query_selector("a[href]")
                    name     = (await name_el.inner_text()).strip() if name_el else ""
                    href     = await login_el.get_attribute("href") if login_el else ""
                    profile  = f"https://github.com{href}" if href and href.startswith("/") else href

                    results.append(_normalized(
                        name=name,
                        role="Engineer / Contributor",
                        company=org_name,
                        url=profile or url,
                        source="GitHub",
                        snippet=f"GitHub member of {org_name}",
                    ))
                except Exception as e:
                    logger.debug(f"[GitHub] member parse error: {e}")
        except Exception as e:
            logger.error(f"[GitHub] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[GitHub] Found {len(results)} members for org '{org_name}'")
        return results

    # ------------------------------------------------------------------ #
    # 5. Crunchbase                                                          #
    # ------------------------------------------------------------------ #
    async def scrape_crunchbase(
        self, keyword: str, funding_stage: str = "", limit: int = 10
    ) -> List[Dict]:
        """
        Scrapes Crunchbase public company search for `keyword`.
        Returns key executives/founders from company cards.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://www.crunchbase.com/search/people/field/persons/facet_ids/{keyword.replace(' ', '-').lower()}"
            # Fallback: use the simpler org search
            url = f"https://www.crunchbase.com/search/organizations/field/organizations/short_description/{keyword.replace(' ', '%20')}"
            logger.info(f"[Crunchbase] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await _delay(3, 6)

            # Crunchbase is heavily JS-rendered; extract what's visible
            cards = await page.query_selector_all("cb-organization-card, [data-testid='search-result']")
            if not cards:
                cards = await page.query_selector_all("h4 a, .identifier-label")

            for card in cards[:limit]:
                try:
                    link_el = await card.query_selector("a")
                    text    = (await card.inner_text()).strip()
                    href    = await link_el.get_attribute("href") if link_el else ""
                    full_url = f"https://www.crunchbase.com{href}" if href and href.startswith("/") else href

                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    name    = lines[0] if lines else text[:80]
                    snippet = " | ".join(lines[1:3]) if len(lines) > 1 else ""

                    results.append(_normalized(
                        name=name,
                        role="Founder / Executive",
                        company=name,
                        url=full_url or url,
                        source="Crunchbase",
                        snippet=snippet,
                    ))
                except Exception as e:
                    logger.debug(f"[Crunchbase] card parse error: {e}")
        except Exception as e:
            logger.error(f"[Crunchbase] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[Crunchbase] Found {len(results)} results for '{keyword}'")
        return results

    # ------------------------------------------------------------------ #
    # 6. Wellfound (AngelList Talent)                                        #
    # ------------------------------------------------------------------ #
    async def scrape_wellfound(self, role: str, keyword: str = "", limit: int = 10) -> List[Dict]:
        """
        Scrapes wellfound.com startup jobs/roles matching `role` and optional `keyword`.
        Returns startup employees and founders for each matching company.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            query = f"{role} {keyword}".strip().replace(" ", "%20")
            url = f"https://wellfound.com/jobs?q={query}"
            logger.info(f"[Wellfound] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await _delay(2, 5)

            job_cards = await page.query_selector_all("[data-test='StartupResult'], .job-listing, article")
            for card in job_cards[:limit]:
                try:
                    company_el = await card.query_selector("h2, h3, .startup-link")
                    role_el    = await card.query_selector(".role, [data-test='JobListingJobTitle']")
                    link_el    = await card.query_selector("a")

                    company_name = (await company_el.inner_text()).strip() if company_el else ""
                    role_name    = (await role_el.inner_text()).strip()    if role_el    else role
                    href         = await link_el.get_attribute("href")     if link_el    else ""
                    full_url     = f"https://wellfound.com{href}" if href and href.startswith("/") else href

                    results.append(_normalized(
                        name=company_name,
                        role=role_name,
                        company=company_name,
                        url=full_url or url,
                        source="Wellfound",
                        snippet=f"{role_name} position at {company_name}",
                    ))
                except Exception as e:
                    logger.debug(f"[Wellfound] card parse error: {e}")
        except Exception as e:
            logger.error(f"[Wellfound] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[Wellfound] Found {len(results)} results for '{role}'")
        return results

    # ------------------------------------------------------------------ #
    # 7. YC Startup Directory                                               #
    # ------------------------------------------------------------------ #
    async def scrape_yc_directory(self, keyword: str, batch: str = "", limit: int = 10) -> List[Dict]:
        """
        Scrapes ycombinator.com/companies filtered by `keyword` and optional `batch`.
        Returns YC-backed company founders as prospects.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://www.ycombinator.com/companies?q={keyword.replace(' ', '+')}"
            if batch:
                url += f"&batch={batch}"
            logger.info(f"[YC] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await _delay(2, 5)

            cards = await page.query_selector_all("._company_86jzd_338, a[class*='company']")
            if not cards:
                cards = await page.query_selector_all("li._companyCard")

            for card in cards[:limit]:
                try:
                    name_el    = await card.query_selector("span._coName_86jzd_453, h4")
                    desc_el    = await card.query_selector("span._coDescription_86jzd_478, p")
                    batch_el   = await card.query_selector("._batch_86jzd_492, span[class*='batch']")
                    link_el    = await card.query_selector("a")

                    name    = (await name_el.inner_text()).strip()  if name_el  else ""
                    desc    = (await desc_el.inner_text()).strip()  if desc_el  else ""
                    batch_v = (await batch_el.inner_text()).strip() if batch_el else ""
                    href    = await link_el.get_attribute("href")   if link_el  else ""
                    full_url = f"https://www.ycombinator.com{href}" if href and href.startswith("/") else href

                    results.append(_normalized(
                        name=name,
                        role="Founder / CEO",
                        company=name,
                        url=full_url or url,
                        source="YC Directory",
                        snippet=desc,
                        extra={"yc_batch": batch_v},
                    ))
                except Exception as e:
                    logger.debug(f"[YC] card parse error: {e}")
        except Exception as e:
            logger.error(f"[YC] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[YC] Found {len(results)} companies for '{keyword}'")
        return results

    # ------------------------------------------------------------------ #
    # 8. AngelList / Angel.co                                               #
    # ------------------------------------------------------------------ #
    async def scrape_angellist(self, market: str, role: str = "founder", limit: int = 10) -> List[Dict]:
        """
        Scrapes angel.co/people filtered by `market` and `role`.
        Returns investor/founder profiles.
        """
        results = []
        ctx = await self._new_context()
        try:
            page = await ctx.new_page()
            url = f"https://angel.co/people?market={market.replace(' ', '+')}&role={role}"
            logger.info(f"[AngelList] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await _delay(3, 6)

            profiles = await page.query_selector_all(".profile, [class*='ProfileCard'], .s-grid-item")
            for profile in profiles[:limit]:
                try:
                    name_el    = await profile.query_selector("h2, h3, [class*='Name']")
                    role_el    = await profile.query_selector("[class*='role'], [class*='title']")
                    company_el = await profile.query_selector("[class*='company'], [class*='org']")
                    link_el    = await profile.query_selector("a")

                    name_txt    = (await name_el.inner_text()).strip()    if name_el    else ""
                    role_txt    = (await role_el.inner_text()).strip()    if role_el    else role
                    company_txt = (await company_el.inner_text()).strip() if company_el else ""
                    href        = await link_el.get_attribute("href")     if link_el    else ""
                    full_url    = f"https://angel.co{href}" if href and href.startswith("/") else href

                    results.append(_normalized(
                        name=name_txt,
                        role=role_txt,
                        company=company_txt,
                        url=full_url or url,
                        source="AngelList",
                        snippet=f"{role_txt} in {market}",
                    ))
                except Exception as e:
                    logger.debug(f"[AngelList] profile parse error: {e}")
        except Exception as e:
            logger.error(f"[AngelList] scrape error: {e}")
        finally:
            await ctx.close()

        logger.info(f"[AngelList] Found {len(results)} profiles for market '{market}'")
        return results

    # ------------------------------------------------------------------ #
    # Parallel runner (used internally by router service)                   #
    # ------------------------------------------------------------------ #
    async def run_scrapers(self, scraper_calls: List[Dict]) -> List[Dict]:
        """
        Run multiple scrapers in parallel.
        `scraper_calls` is a list of dicts: { "scraper": str, "kwargs": dict }
        Returns merged, deduplicated results.
        """
        scraper_map = {
            "product_hunt":       self.scrape_product_hunt,
            "g2":                 self.scrape_g2_reviews,
            "hacker_news":        self.scrape_hacker_news_hiring,
            "github":             self.scrape_github_org,
            "crunchbase":         self.scrape_crunchbase,
            "wellfound":          self.scrape_wellfound,
            "yc_directory":       self.scrape_yc_directory,
            "angellist":          self.scrape_angellist,
        }

        tasks = []
        for call in scraper_calls:
            fn = scraper_map.get(call.get("scraper"))
            if fn:
                tasks.append(fn(**call.get("kwargs", {})))
            else:
                logger.warning(f"Unknown scraper: {call.get('scraper')}")

        if not tasks:
            return []

        nested_results = await asyncio.gather(*tasks, return_exceptions=True)

        merged = []
        seen_urls = set()
        seen_names = set()

        for batch in nested_results:
            if isinstance(batch, Exception):
                logger.error(f"Scraper task failed: {batch}")
                continue
            for r in batch:
                key_url  = r.get("url", "")
                key_name = (r.get("name", "") + r.get("company", "")).lower().strip()
                if key_url in seen_urls or (key_name and key_name in seen_names):
                    continue
                seen_urls.add(key_url)
                if key_name:
                    seen_names.add(key_name)
                merged.append(r)

        logger.info(f"[run_scrapers] Merged {len(merged)} unique results from {len(tasks)} scrapers")
        return merged
