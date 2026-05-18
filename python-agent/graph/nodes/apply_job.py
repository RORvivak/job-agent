import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

from ..state import JobAgentState
from portals.linkedin.applier import LinkedInApplier
from portals.linkedin.session import get_context, save_session
from services.rails_client import update_application


async def _apply_async(state: JobAgentState) -> dict:
    user_id = state.get("user_id", 0)
    job = state.get("current_job", {})
    resume_path = state.get("customized_resume_path") or state.get("resume_path", "")
    cover_letter_path = state.get("cover_letter_path", "")
    app_id = state.get("application_id", 0)
    prefs = state.get("preferences", {})
    parsed = state.get("parsed_resume", {})

    candidate = {
        "name": parsed.get("contact", {}).get("name", ""),
        "email": parsed.get("contact", {}).get("email", ""),
        "phone": parsed.get("contact", {}).get("phone", ""),
        "linkedin": parsed.get("contact", {}).get("linkedin", ""),
        "github": parsed.get("contact", {}).get("github", ""),
        "location": parsed.get("contact", {}).get("location", ""),
        "years_experience": prefs.get("years_experience", ""),
        "expected_salary": prefs.get("salary_max", ""),
        "notice_period": "30 days",
        "work_authorization": "Yes",
        "remote_preference": prefs.get("remote_preference", "Remote"),
    }

    async with async_playwright() as p:
        browser, context, page = await get_context(p, user_id)
        try:
            portal = job.get("portal", "linkedin")
            logger.info(f"[apply_job] applying | portal={portal} job={job.get('title')} @ {job.get('company')}")
            if portal == "linkedin":
                applier = LinkedInApplier()
                result = await applier.apply(page, job, resume_path, cover_letter_path, candidate, application_id=app_id)
            else:
                logger.error(f"[apply_job] portal not implemented | portal={portal}")
                return {"error": f"Portal {portal} not implemented"}

            await save_session(context, user_id)
            logger.info(f"[apply_job] result | success={result.success} error={result.error} external_url={result.external_url}")
            return {
                "success": result.success,
                "external_url": result.external_url,
                "error": result.error,
                "screenshot_path": result.screenshot_path,
            }
        finally:
            await browser.close()


def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job", {})
    logger.info(f"[apply_job] starting | job={job.get('title')} @ {job.get('company')}")
    try:
        result = asyncio.run(_apply_async(state))
        state["apply_result"] = result
    except Exception as e:
        logger.error(f"[apply_job] error | {e}")
        state["apply_result"] = {"error": str(e), "success": False}
        state.setdefault("errors", []).append({"step": "apply_job", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "apply_job", "status": "done"})
    logger.info(f"[apply_job] done | result={state.get('apply_result', {}).get('success')}")
    return state
