import asyncio
import os
from datetime import datetime
from loguru import logger


async def _find_and_fill(page, hints: list[str], value: str, label: str) -> bool:
    """Try multiple selector strategies to find and fill a text/textarea input."""
    for hint in hints:
        hint_lower = hint.lower()
        selectors = [
            f'input[name*="{hint}"]',
            f'input[id*="{hint}"]',
            f'input[placeholder*="{hint}"]',
            f'textarea[name*="{hint}"]',
            f'textarea[id*="{hint}"]',
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.count():
                    await el.fill(value)
                    return True
            except Exception:
                continue

    # Label-text-adjacent fallback: find label containing the field label text
    try:
        label_el = page.locator(f'label:has-text("{label}")').first
        if await label_el.count():
            for_id = await label_el.get_attribute("for")
            if for_id:
                inp = page.locator(f"#{for_id}").first
                if await inp.count():
                    await inp.fill(value)
                    return True
    except Exception:
        pass

    return False


async def _find_and_select(page, hints: list[str], value: str) -> bool:
    for hint in hints:
        selectors = [f'select[name*="{hint}"]', f'select[id*="{hint}"]']
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.count():
                    options = await el.locator("option").all_inner_texts()
                    for opt in options:
                        if value.lower() in opt.lower():
                            await el.select_option(label=opt)
                            return True
                    # Try value= directly as fallback
                    await el.select_option(value=value)
                    return True
            except Exception:
                continue
    return False


async def _find_and_upload(page, hints: list[str], file_path: str) -> bool:
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"[plan_executor] upload skipped — file not found: {file_path}")
        return False

    # Try hint-matched file inputs first
    for hint in hints:
        selectors = [f'input[type="file"][name*="{hint}"]', f'input[type="file"][id*="{hint}"]']
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.count():
                    await el.set_input_files(file_path)
                    return True
            except Exception:
                continue

    # Fallback: first visible file input
    try:
        inputs = await page.locator('input[type="file"]').all()
        for inp in inputs:
            try:
                await inp.set_input_files(file_path)
                return True
            except Exception:
                continue
    except Exception:
        pass

    return False


async def _submit(page, label: str) -> bool:
    # Try button with matching text first
    try:
        btn = page.locator(f'button:has-text("{label}"), input[type="submit"][value*="{label}"]').first
        if await btn.count():
            await btn.click()
            return True
    except Exception:
        pass

    # Generic submit fallback
    try:
        btn = page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Apply")').first
        if await btn.count():
            await btn.click()
            return True
    except Exception:
        pass

    return False


async def execute_plan(page, plan: dict, resume_path: str, cover_letter_path: str, screenshots_dir: str, app_id: int) -> dict:
    os.makedirs(screenshots_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    submitted = False

    try:
        actions = plan.get("actions", [])
        for action in actions:
            act = action.get("action")
            label = action.get("label", "")
            value = action.get("value", "")
            hints = action.get("hints", [])

            await asyncio.sleep(0.3)

            if act == "fill":
                ok = await _find_and_fill(page, hints, value, label)
                logger.info(f"[plan_executor] fill '{label}' => {'ok' if ok else 'not found'}")

            elif act == "select":
                ok = await _find_and_select(page, hints, value)
                logger.info(f"[plan_executor] select '{label}' => {'ok' if ok else 'not found'}")

            elif act == "upload":
                file = resume_path if "resume" in label.lower() or "cv" in label.lower() else cover_letter_path
                # Use value directly if it's a real path (plan_application replaces placeholders)
                if value and os.path.exists(value):
                    file = value
                ok = await _find_and_upload(page, hints, file)
                logger.info(f"[plan_executor] upload '{label}' => {'ok' if ok else 'not found'}")

            elif act == "submit":
                await asyncio.sleep(1)
                ok = await _submit(page, label)
                if ok:
                    submitted = True
                    await asyncio.sleep(3)
                    logger.info(f"[plan_executor] submitted form")
                else:
                    logger.warning(f"[plan_executor] submit button not found for label='{label}'")

        screenshot_path = os.path.join(screenshots_dir, f"submitted_{app_id}_{ts}.png")
        await page.screenshot(path=screenshot_path, full_page=True)

        return {"success": submitted, "screenshot_path": screenshot_path, "error": "" if submitted else "submit_button_not_found"}

    except Exception as e:
        logger.error(f"[plan_executor] error | {e}")
        screenshot_path = os.path.join(screenshots_dir, f"error_{app_id}_{ts}.png")
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
        except Exception:
            screenshot_path = ""
        return {"success": False, "screenshot_path": screenshot_path, "error": str(e)}
