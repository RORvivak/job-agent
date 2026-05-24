from loguru import logger

from ..state import JobAgentState
from portals.remotive.scraper import fetch_jobs as _fetch


def run(state: JobAgentState) -> JobAgentState:
    prefs = state.get("preferences", {})
    logger.info("[fetch_jobs] fetching jobs from Remotive")
    jobs = _fetch(prefs, limit=20)
    logger.info(f"[fetch_jobs] done | count={len(jobs)}")
    state["jobs"] = jobs
    state.setdefault("step_log", []).append({"step": "fetch_jobs", "status": "done", "count": len(jobs)})
    return state
