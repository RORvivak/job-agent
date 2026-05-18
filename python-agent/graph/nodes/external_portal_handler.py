import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

from ..state import JobAgentState
from automation.form_filler import fill_form
from automation.captcha_handler import detect_and_handle, save_screenshot
from portals.linkedin.session import get_context, save_session

SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR", "storage/screenshots")


async def _handle_external_async(state: JobAgentState) -> dict:
    user_id = state.get("user_id", 0)
    apply_result = state.get("apply_result", {})
    external_url = apply_result.get("external_url", "")
    app_id = state.get("application_id", 0)
    prefs = state.get("preferences", {})
    parsed = state.get("parsed_resume", {})

    logger.info(f"[external_portal_handler] navigating | url={external_url}")

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

    resume_path = state.get("customized_resume_path") or state.get("resume_path", "")

    async with async_playwright() as p:
        browser, context, page = await get_context(p, user_id)
        try:
            await page.goto(external_url, wait_until="domcontentloaded", timeout=20000)

            captcha = await detect_and_handle(page, app_id, SCREENSHOTS_DIR)
            if captcha["captcha_detected"]:
                logger.warning("[external_portal_handler] captcha detected")
                return {"success": False, "error": "captcha_on_external", "screenshot_path": captcha["screenshot_path"]}

            logger.info("[external_portal_handler] filling form")
            await fill_form(page, candidate)

            if resume_path:
                file_inputs = await page.locator("input[type='file']").all()
                for fi in file_inputs:
                    try:
                        await fi.set_input_files(resume_path)
                        logger.info("[external_portal_handler] resume uploaded")
                        break
                    except Exception:
                        continue

            submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit'), button:has-text('Apply')").first
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await asyncio.sleep(3)
                screenshot = await save_screenshot(page, "external_submitted", app_id, SCREENSHOTS_DIR)
                logger.info("[external_portal_handler] submitted successfully")
                return {"success": True, "screenshot_path": screenshot}

            screenshot = await save_screenshot(page, "external_no_submit", app_id, SCREENSHOTS_DIR)
            logger.warning("[external_portal_handler] no submit button found")
            return {"success": False, "error": "no_submit_button", "screenshot_path": screenshot}
        finally:
            await browser.close()


def run(state: JobAgentState) -> JobAgentState:
    logger.info("[external_portal_handler] starting")
    try:
        result = asyncio.run(_handle_external_async(state))
        state["apply_result"] = {**state.get("apply_result", {}), **result}
    except Exception as e:
        logger.error(f"[external_portal_handler] error | {e}")
        state.setdefault("errors", []).append({"step": "external_portal_handler", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "external_portal_handler", "status": "done"})
    logger.info(f"[external_portal_handler] done | success={state.get('apply_result', {}).get('success')}")
    return state
