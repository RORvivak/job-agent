import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

from ..state import JobAgentState
from portals.linkedin.scraper import LinkedInScraper
from portals.linkedin.session import get_context, save_session, is_logged_in


async def _search_async(state: JobAgentState) -> list[dict]:
    prefs = state.get("preferences", {})
    user_id = state.get("user_id", 0)
    limit = int(os.environ.get("MAX_JOBS_TO_APPLY_PER_DAY", "10"))

    async with async_playwright() as p:
        browser, context, page = await get_context(p, user_id)
        try:
            logger.info("[search_jobs] checking linkedin login status")
            logged = await is_logged_in(page)
            if not logged:
                logger.info("[search_jobs] not logged in — attempting login")
                email = os.environ.get("LINKEDIN_EMAIL", "")
                password = os.environ.get("LINKEDIN_PASSWORD", "")
                await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                email_input = page.locator("input[type='email']")
                if await email_input.count() > 0:
                    logger.info("[search_jobs] filling login form")
                    await email_input.fill(email)
                    await page.locator("input[type='password']").fill(password)
                    await page.click("button[type='submit']")
                else:
                    logger.warning("[search_jobs] email input not found — waiting for manual login")

                try:
                    await page.wait_for_url("**/feed/**", timeout=120000)
                    logger.info("[search_jobs] login successful — on feed")
                    await save_session(context, user_id)
                except Exception:
                    logger.error("[search_jobs] login failed — not on feed after 2 minutes. Run login.py first.")
                    return []
            else:
                logger.info("[search_jobs] already logged in")

            logger.info(f"[search_jobs] searching jobs | roles={prefs.get('desired_roles')} limit={limit}")
            scraper = LinkedInScraper()
            jobs = await scraper.search(page, prefs, limit=limit)
            await save_session(context, user_id)
            logger.info(f"[search_jobs] found {len(jobs)} jobs")
            return jobs
        finally:
            await browser.close()


def run(state: JobAgentState) -> JobAgentState:
    logger.info(f"[search_jobs] starting | user_id={state.get('user_id')}")
    try:
        jobs = asyncio.run(_search_async(state))
        state["jobs"] = jobs
    except Exception as e:
        logger.error(f"[search_jobs] error | {e}")
        state.setdefault("errors", []).append({"step": "search_jobs", "msg": str(e)})
        state["jobs"] = []

    logger.info(f"[search_jobs] done | jobs={len(state.get('jobs', []))}")
    state.setdefault("step_log", []).append({"step": "search_jobs", "status": "done", "count": len(state.get("jobs", []))})
    return state
