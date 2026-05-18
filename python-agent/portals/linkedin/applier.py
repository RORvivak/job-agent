import asyncio
import random
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from loguru import logger

from portals.base_portal import ApplyResult
from automation.form_filler import fill_form
from automation.captcha_handler import detect_and_handle, save_screenshot


SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR", "storage/screenshots")


class LinkedInApplier:
    async def apply(self, page, job: dict, resume_path: str,
                    cover_letter_path: str, candidate: dict,
                    application_id: int = 0) -> ApplyResult:
        try:
            await page.goto(job["job_url"], wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(random.uniform(1.5, 3))

            captcha = await detect_and_handle(page, application_id, SCREENSHOTS_DIR)
            if captcha["captcha_detected"]:
                return ApplyResult(error="captcha_detected", screenshot_path=captcha["screenshot_path"])

            # Find Easy Apply button by text — LinkedIn hashes class names so text is reliable
            easy_apply_btn = page.get_by_role("button", name="Easy Apply", exact=False).first
            if await easy_apply_btn.count() == 0:
                # Fallback to old stable selectors
                easy_apply_btn = page.locator(
                    "button[aria-label*='Easy Apply'], button.jobs-apply-button"
                ).first

            if await easy_apply_btn.count() == 0:
                external_url = await self._detect_external(page)
                if external_url:
                    logger.info(f"[applier] external apply URL: {external_url}")
                    return ApplyResult(external_url=external_url)
                logger.warning(f"[applier] no apply button | url={page.url} title={await page.title()}")
                return ApplyResult(error="no_apply_button_found")

            await easy_apply_btn.click()
            await asyncio.sleep(random.uniform(1, 2))

            result = await self._handle_easy_apply_modal(page, resume_path, cover_letter_path, candidate, application_id)
            return result
        except Exception as e:
            screenshot = await save_screenshot(page, "error", application_id, SCREENSHOTS_DIR)
            return ApplyResult(error=str(e), screenshot_path=screenshot)

    async def _handle_easy_apply_modal(self, page, resume_path: str,
                                        cover_letter_path: str, candidate: dict,
                                        application_id: int) -> ApplyResult:
        max_steps = 10
        step = 0

        while step < max_steps:
            captcha = await detect_and_handle(page, application_id, SCREENSHOTS_DIR)
            if captcha["captcha_detected"]:
                return ApplyResult(error="captcha_in_modal", screenshot_path=captcha["screenshot_path"])

            await fill_form(page, candidate)

            if resume_path and await page.locator("input[type='file']").count() > 0:
                await self._upload_file(page, resume_path)

            submit_btn = page.get_by_role("button", name="Submit application", exact=False).first
            if await submit_btn.count() == 0:
                submit_btn = page.locator("button[aria-label='Submit application']").first
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await asyncio.sleep(random.uniform(2, 4))
                screenshot = await save_screenshot(page, "submitted", application_id, SCREENSHOTS_DIR)
                return ApplyResult(success=True, screenshot_path=screenshot)

            next_btn = page.get_by_role("button", name="Continue to next step", exact=False).first
            if await next_btn.count() == 0:
                next_btn = page.get_by_role("button", name="Review your application", exact=False).first
            if await next_btn.count() == 0:
                next_btn = page.locator(
                    "button[aria-label='Continue to next step'], button[aria-label='Review your application']"
                ).first
            if await next_btn.count() > 0:
                await next_btn.click()
                await asyncio.sleep(random.uniform(1, 2))
                step += 1
                continue

            break

        screenshot = await save_screenshot(page, "stalled", application_id, SCREENSHOTS_DIR)
        return ApplyResult(error="modal_stalled", screenshot_path=screenshot)

    async def _upload_file(self, page, file_path: str) -> None:
        file_input = page.locator("input[type='file']").first
        if await file_input.count() > 0 and Path(file_path).exists():
            await file_input.set_input_files(file_path)
            await asyncio.sleep(random.uniform(1, 2))

    async def _detect_external(self, page) -> str:
        try:
            # LinkedIn wraps external apply URLs in safety redirects
            links = await page.locator("a[href*='linkedin.com/safety/go']").all()
            for link in links:
                href = await link.get_attribute("href") or ""
                decoded = self._decode_linkedin_url(href)
                if decoded:
                    return decoded
        except Exception:
            pass
        return ""

    def _decode_linkedin_url(self, href: str) -> str:
        if not href:
            return ""
        if "linkedin.com/safety/go" in href:
            parsed = urlparse(href)
            url_param = parse_qs(parsed.query).get("url", [""])[0]
            return unquote(url_param) if url_param else ""
        if href.startswith("http") and "linkedin.com" not in href:
            return href
        return ""
