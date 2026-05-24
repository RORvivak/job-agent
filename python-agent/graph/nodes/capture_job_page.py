import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

from ..state import JobAgentState
from automation.page_capturer import capture_apply_page
from services.rails_client import create_application

SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR", "storage/screenshots")
HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"


async def _run_async(state: JobAgentState) -> dict:
    job = state.get("current_job", {})
    app_id = state.get("application_id") or 0
    job_url = job.get("job_url", "")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            return await capture_apply_page(page, job_url, app_id, SCREENSHOTS_DIR)
        finally:
            await browser.close()


def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job", {})
    logger.info(f"[capture_job_page] starting | job={job.get('title')} @ {job.get('company')}")

    if not state.get("application_id") and job:
        app_id = create_application(state.get("user_id", 0), job, state.get("correlation_id", ""))
        if app_id:
            state["application_id"] = app_id
            logger.info(f"[capture_job_page] application record created early | app_id={app_id}")

    try:
        result = asyncio.run(_run_async(state))
        state["job_screenshots"] = result.get("screenshots", [])
        state["apply_url"] = result.get("apply_url", "")
        logger.info(f"[capture_job_page] done | screenshots={len(state['job_screenshots'])} apply_url={state['apply_url']}")
    except Exception as e:
        logger.error(f"[capture_job_page] error | {e}")
        state["job_screenshots"] = []
        state["apply_url"] = ""
        state.setdefault("errors", []).append({"step": "capture_job_page", "msg": str(e)})
    state.setdefault("step_log", []).append({"step": "capture_job_page", "status": "done"})
    return state
