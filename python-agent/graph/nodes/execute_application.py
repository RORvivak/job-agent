import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

from ..state import JobAgentState
from automation.plan_executor import execute_plan

SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR", "storage/screenshots")
HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"


async def _run_async(state: JobAgentState) -> dict:
    apply_url = state.get("apply_url", "")
    form_plan = state.get("form_plan", {})
    resume_path = state.get("customized_resume_path") or state.get("resume_path", "")
    cover_letter_path = state.get("cover_letter_path", "")
    app_id = state.get("application_id") or 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            if apply_url:
                await page.goto(apply_url, wait_until="domcontentloaded", timeout=20000)
            return await execute_plan(page, form_plan, resume_path, cover_letter_path, SCREENSHOTS_DIR, app_id)
        finally:
            await browser.close()


def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job", {})
    logger.info(f"[execute_application] starting | job={job.get('title')} @ {job.get('company')}")
    try:
        result = asyncio.run(_run_async(state))
        state["apply_result"] = {
            "success": result.get("success", False),
            "screenshot_path": result.get("screenshot_path", ""),
            "error": result.get("error", ""),
            "external_url": "",
        }
        logger.info(f"[execute_application] done | success={result.get('success')} error={result.get('error')}")
    except Exception as e:
        logger.error(f"[execute_application] error | {e}")
        state["apply_result"] = {"success": False, "screenshot_path": "", "error": str(e), "external_url": ""}
        state.setdefault("errors", []).append({"step": "execute_application", "msg": str(e)})
    state.setdefault("step_log", []).append({"step": "execute_application", "status": "done"})
    return state
