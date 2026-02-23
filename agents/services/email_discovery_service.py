"""
Email Discovery & Verification Service
=======================================
Generates email candidates using 10 common enterprise patterns from
(first_name, last_name, company_domain) and verifies them via:
  1. DNS MX record check  — fast domain validation
  2. SMTP RCPT TO probe   — no email sent; just checks if address is accepted
  3. Confidence scoring   — pattern weight × SMTP result

Optional: Hunter.io API fallback if HUNTER_API_KEY is set.
"""

import asyncio
import logging
import os
import re
import smtplib
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import dns.resolver
import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EmailCandidate:
    address: str
    pattern_name: str
    pattern_rank: int          # 1 = most common globally
    confidence: str = "unknown"  # "verified" | "likely" | "unverifiable" | "invalid"
    smtp_code: Optional[int] = None
    note: str = ""


# ---------------------------------------------------------------------------
# 10 canonical email patterns (ordered by global enterprise frequency)
# ---------------------------------------------------------------------------

PATTERNS = [
    # rank, label, lambda(f, l, fi, li) -> local_part
    (1,  "first.last",   lambda f, l, fi, li: f"{f}.{l}"),
    (2,  "first",        lambda f, l, fi, li: f"{f}"),
    (3,  "flast",        lambda f, l, fi, li: f"{fi}{l}"),
    (4,  "firstlast",    lambda f, l, fi, li: f"{f}{l}"),
    (5,  "last",         lambda f, l, fi, li: f"{l}"),
    (6,  "first_last",   lambda f, l, fi, li: f"{f}_{l}"),
    (7,  "f.last",       lambda f, l, fi, li: f"{fi}.{l}"),
    (8,  "firstl",       lambda f, l, fi, li: f"{f}{li}"),
    (9,  "lastfirst",    lambda f, l, fi, li: f"{l}{f}"),
    (10, "last.first",   lambda f, l, fi, li: f"{l}.{f}"),
]

# Pattern confidence weights (how likely each pattern is to be used)
PATTERN_WEIGHTS = {1: 0.9, 2: 0.8, 3: 0.75, 4: 0.65, 5: 0.6,
                   6: 0.55, 7: 0.70, 8: 0.45, 9: 0.35, 10: 0.40}


class EmailDiscoveryService:
    """Discovers and verifies email addresses for a given prospect."""

    def __init__(self):
        self.hunter_api_key = os.getenv("HUNTER_API_KEY")
        self.smtp_timeout = 10  # seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_email_patterns(
        self, first_name: str, last_name: str, domain: str
    ) -> List[EmailCandidate]:
        """Generate all 10 email pattern candidates. Pure, no I/O."""
        f  = self._clean(first_name)
        l  = self._clean(last_name)
        fi = f[0] if f else ""
        li = l[0] if l else ""

        candidates = []
        for rank, label, pattern_fn in PATTERNS:
            local = pattern_fn(f, l, fi, li)
            if local:
                candidates.append(EmailCandidate(
                    address=f"{local}@{domain}",
                    pattern_name=label,
                    pattern_rank=rank,
                ))
        return candidates

    async def check_mx_records(self, domain: str) -> bool:
        """Check whether `domain` has MX records. Returns True/False."""
        try:
            loop = asyncio.get_event_loop()
            records = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, "MX")
            )
            return len(records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.DNSException):
            return False
        except Exception as e:
            logger.warning(f"MX check failed for {domain}: {e}")
            return False

    async def verify_smtp(self, email: str, domain: str) -> Tuple[Optional[int], str]:
        """
        Probe the MX server with RCPT TO without sending any email.
        Returns (smtp_code, note) where smtp_code is None on connection failure.
        250 = accepted, 550/551 = rejected, None = unverifiable (server blocked)
        """
        try:
            # Resolve MX
            loop = asyncio.get_event_loop()
            mx_records = await loop.run_in_executor(
                None, lambda: sorted(
                    dns.resolver.resolve(domain, "MX"),
                    key=lambda r: r.preference
                )
            )
            if not mx_records:
                return None, "No MX records"

            mx_host = str(mx_records[0].exchange).rstrip(".")

            def _smtp_probe():
                try:
                    with smtplib.SMTP(mx_host, 25, timeout=self.smtp_timeout) as server:
                        server.ehlo("probe.ai-sdr.local")
                        code, _ = server.mail("probe@ai-sdr.local")
                        if code != 250:
                            return None, "MAIL FROM rejected"
                        code, msg = server.rcpt(email)
                        return code, msg.decode("utf-8", errors="ignore")
                except smtplib.SMTPConnectError:
                    return None, "SMTP connect failed"
                except smtplib.SMTPServerDisconnected:
                    return None, "Server disconnected early"
                except socket.timeout:
                    return None, "Connection timed out"
                except Exception as ex:
                    return None, str(ex)

            result = await loop.run_in_executor(None, _smtp_probe)
            return result

        except Exception as e:
            return None, f"SMTP probe error: {e}"

    async def find_best_email(
        self,
        first_name: str,
        last_name: str,
        company_domain: str,
        max_candidates: int = 5,
    ) -> List[dict]:
        """
        Full pipeline:
          1. Generate 10 candidates
          2. MX check (abort early if domain is dead)
          3. SMTP probe top N candidates (default 5)
          4. Try Hunter.io fallback if key available
          5. Return sorted results with confidence scores
        """
        domain = company_domain.lower().strip().lstrip("www.").lstrip("http://").lstrip("https://")

        # Step 1 – Generate patterns
        candidates = self.generate_email_patterns(first_name, last_name, domain)
        logger.info(f"Generated {len(candidates)} email patterns for {first_name} {last_name} @ {domain}")

        # Step 2 – MX check
        has_mx = await self.check_mx_records(domain)
        if not has_mx:
            logger.warning(f"Domain {domain} has no MX records — marking all invalid")
            for c in candidates:
                c.confidence = "invalid"
                c.note = "Domain has no MX records"
            return [self._candidate_to_dict(c) for c in candidates]

        # Step 3 – Hunter.io lookup (primary if key available)
        hunter_email = None
        if self.hunter_api_key:
            hunter_email = await self._hunter_lookup(first_name, last_name, domain)

        # Step 4 – SMTP probe top N candidates
        to_probe = candidates[:max_candidates]
        probe_tasks = [self.verify_smtp(c.address, domain) for c in to_probe]
        probe_results = await asyncio.gather(*probe_tasks, return_exceptions=True)

        for i, candidate in enumerate(to_probe):
            result = probe_results[i]
            if isinstance(result, Exception):
                code, note = None, str(result)
            else:
                code, note = result

            candidate.smtp_code = code
            candidate.note = note

            if hunter_email and candidate.address.lower() == hunter_email.lower():
                candidate.confidence = "verified"
                candidate.note = "Confirmed by Hunter.io"
            elif code == 250:
                candidate.confidence = "verified"
            elif code in (550, 551, 552, 553):
                candidate.confidence = "invalid"
            elif code is None:
                # Server blocked probe — use pattern weight for confidence
                weight = PATTERN_WEIGHTS.get(candidate.pattern_rank, 0.3)
                candidate.confidence = "likely" if weight >= 0.65 else "unverifiable"
            else:
                candidate.confidence = "unverifiable"

        # For non-probed candidates (rank > max_candidates), mark as unverifiable
        for candidate in candidates[max_candidates:]:
            weight = PATTERN_WEIGHTS.get(candidate.pattern_rank, 0.3)
            candidate.confidence = "likely" if weight >= 0.7 else "unverifiable"
            candidate.note = "Not probed (lower priority pattern)"

        # Sort: verified first, then by pattern rank
        order = {"verified": 0, "likely": 1, "unverifiable": 2, "invalid": 3, "unknown": 4}
        candidates.sort(key=lambda c: (order.get(c.confidence, 4), c.pattern_rank))

        return [self._candidate_to_dict(c) for c in candidates]

    async def enrich_prospect_email(self, prospect: dict) -> dict:
        """
        Convenience wrapper: given a prospect dict with 'name' and 'company',
        tries to find the company's domain and discover the email.
        Returns the prospect dict with an 'email_candidates' key added.
        """
        name = prospect.get("name", "")
        company = prospect.get("company", "")

        # Try to split name into first/last
        parts = name.strip().split()
        if len(parts) < 2:
            prospect["email_candidates"] = []
            return prospect

        first_name = parts[0]
        last_name = parts[-1]

        # Attempt to derive domain from company name (best-effort)
        domain = prospect.get("email_domain") or self._guess_domain(company)
        if not domain:
            prospect["email_candidates"] = []
            return prospect

        try:
            candidates = await self.find_best_email(first_name, last_name, domain)
            # Attach top result as primary email if verified/likely
            if candidates:
                top = candidates[0]
                if top["confidence"] in ("verified", "likely"):
                    prospect["email"] = top["address"]
                    prospect["email_confidence"] = top["confidence"]
            prospect["email_candidates"] = candidates
        except Exception as e:
            logger.error(f"Email enrichment failed for {name}: {e}")
            prospect["email_candidates"] = []

        return prospect

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clean(self, name: str) -> str:
        """Lowercase, remove special chars, trim."""
        return re.sub(r"[^a-z0-9]", "", name.lower().strip())

    def _candidate_to_dict(self, c: EmailCandidate) -> dict:
        return {
            "address": c.address,
            "pattern": c.pattern_name,
            "pattern_rank": c.pattern_rank,
            "confidence": c.confidence,
            "smtp_code": c.smtp_code,
            "note": c.note,
        }

    def _guess_domain(self, company_name: str) -> Optional[str]:
        """
        Very rough heuristic: turns 'Acme Corp' into 'acme.com'.
        In production this should be replaced by clearbit/hunter enrichment.
        """
        if not company_name:
            return None
        # Remove common noise words
        noise = {"inc", "llc", "ltd", "corp", "corporation", "co", "company",
                 "group", "solutions", "technologies", "tech", "labs", "ai"}
        words = [w for w in re.sub(r"[^a-z0-9 ]", "", company_name.lower()).split()
                 if w not in noise]
        if not words:
            return None
        return f"{words[0]}.com"

    async def _hunter_lookup(self, first: str, last: str, domain: str) -> Optional[str]:
        """Call Hunter.io Email Finder API if key is available."""
        if not self.hunter_api_key:
            return None
        url = "https://api.hunter.io/v2/email-finder"
        params = {
            "domain": domain,
            "first_name": first,
            "last_name": last,
            "api_key": self.hunter_api_key,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        email = data.get("data", {}).get("email")
                        if email:
                            logger.info(f"Hunter.io found email: {email}")
                        return email
        except Exception as e:
            logger.warning(f"Hunter.io lookup failed: {e}")
        return None
