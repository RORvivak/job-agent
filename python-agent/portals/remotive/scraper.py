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


def fetch_jobs(prefs: dict, limit: int = 20) -> list[dict]:
    desired_roles = prefs.get("desired_roles", [])
    keywords = [r.lower() for r in desired_roles] if desired_roles else ["engineer", "developer"]

    try:
        resp = httpx.get(REMOTIVE_API, params={"category": "software-dev", "limit": 100}, timeout=15)
        resp.raise_for_status()
        all_jobs = resp.json().get("jobs", [])
    except Exception as e:
        logger.error(f"[remotive_scraper] failed to fetch jobs: {e}")
        return []

    results = []
    for job in all_jobs:
        title = job.get("title", "")
        if not any(kw in title.lower() for kw in keywords):
            continue
        description = _strip_html(job.get("description", ""))[:2000]
        results.append({
            "title": title,
            "company": job.get("company_name", ""),
            "job_url": job.get("url", ""),
            "description": description,
            "portal": "remotive",
        })
        if len(results) >= limit:
            break

    logger.info(f"[remotive_scraper] matched {len(results)} jobs from {len(all_jobs)} total")
    return results
