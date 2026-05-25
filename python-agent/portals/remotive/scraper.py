import re
import html as html_lib
from html.parser import HTMLParser
from loguru import logger
import httpx


REMOTIVE_API = "https://remotive.com/api/remote-jobs"


class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return re.sub(r"\s+", " ", "".join(self._parts)).strip()


def _strip_html(raw: str) -> str:
    parser = _StripHTML()
    parser.feed(html_lib.unescape(raw))
    return parser.get_text()


_STOP_WORDS = {"a", "an", "the", "and", "or", "of", "in", "at", "for", "to", "with", "on"}


def _role_keywords(desired_roles: list[str]) -> list[str]:
    words = set()
    for role in desired_roles:
        for word in role.lower().split():
            if word not in _STOP_WORDS and len(word) > 2:
                words.add(word)
    return list(words) if words else ["engineer", "developer"]


def _score_job(title: str, description: str, role_phrases: list[str],
               role_keywords: list[str], stack_keywords: list[str]) -> float:
    title_lower = title.lower()
    desc_lower = description[:1500].lower()

    # Full phrase match in title is strongest signal
    phrase_hits = sum(2.0 for phrase in role_phrases if phrase in title_lower)
    # Individual keyword match in title
    keyword_hits = sum(1.0 for kw in role_keywords if kw in title_lower)
    # Preferred stack match anywhere in description
    stack_hits = sum(0.4 for kw in stack_keywords if kw in desc_lower or kw in title_lower)

    return phrase_hits + keyword_hits + stack_hits


def fetch_jobs(prefs: dict, limit: int = 20) -> list[dict]:
    desired_roles = prefs.get("desired_roles", [])
    preferred_stack = prefs.get("preferred_stack", [])

    role_phrases = [r.lower() for r in desired_roles]
    role_keywords = _role_keywords(desired_roles)
    stack_keywords = [s.lower() for s in preferred_stack if len(s) > 1]

    logger.info(f"[remotive_scraper] role_phrases={role_phrases} stack_keywords={stack_keywords[:8]}")

    try:
        resp = httpx.get(REMOTIVE_API, params={"category": "software-dev", "limit": 200}, timeout=15)
        resp.raise_for_status()
        all_jobs = resp.json().get("jobs", [])
    except Exception as e:
        logger.error(f"[remotive_scraper] failed to fetch jobs: {e}")
        return []

    scored = []
    for job in all_jobs:
        title = job.get("title", "")
        description = _strip_html(job.get("description", ""))
        score = _score_job(title, description, role_phrases, role_keywords, stack_keywords)
        if score <= 0:
            continue
        scored.append((score, {
            "title": title,
            "company": job.get("company_name", ""),
            "job_url": job.get("url", ""),
            "description": description[:2000],
            "portal": "remotive",
            "location": job.get("candidate_required_location", "Worldwide"),
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [j for _, j in scored[:limit]]
    logger.info(f"[remotive_scraper] matched {len(results)} jobs (scored) from {len(all_jobs)} total")
    return results
