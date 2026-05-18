import os
import time
from pathlib import Path


async def detect_and_handle(page, application_id: int, screenshots_dir: str) -> dict:
    """Detect captcha and save screenshot. Returns action dict."""
    captcha_selectors = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        ".g-recaptcha",
        "#captcha",
        "[class*='captcha']",
        "[id*='captcha']",
    ]

    for sel in captcha_selectors:
        try:
            if await page.locator(sel).count() > 0:
                path = _save_screenshot(page, application_id, screenshots_dir)
                return {
                    "captcha_detected": True,
                    "screenshot_path": path,
                    "action": "paused_captcha",
                }
        except Exception:
            continue

    return {"captcha_detected": False}


def _save_screenshot(page, application_id: int, screenshots_dir: str) -> str:
    import asyncio
    dir_path = Path(screenshots_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = f"captcha_{application_id}_{int(time.time())}.png"
    path = str(dir_path / filename)
    asyncio.get_event_loop().run_until_complete(page.screenshot(path=path))
    return path


async def save_screenshot(page, label: str, application_id, screenshots_dir: str) -> str:
    if not application_id:
        return ""
    dir_path = Path(screenshots_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = f"{label}_{application_id}_{int(time.time())}.png"
    path = str(dir_path / filename)
    await page.screenshot(path=path)
    return path
