import asyncio
import os
from datetime import datetime
from loguru import logger


APPLY_LINK_SELECTORS = [
    'a:has-text("Apply for this job")',
    'a:has-text("Apply now")',
    'a:has-text("Apply Now")',
    'a:has-text("Apply")',
    'a[href*="greenhouse.io"]',
    'a[href*="lever.co"]',
    'a[href*="workable.com"]',
    'a[href*="ashbyhq.com"]',
    'a[href*="jobs."]',
]


async def capture_apply_page(page, job_url: str, app_id: int, screenshots_dir: str) -> dict:
    os.makedirs(screenshots_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    screenshots = []
    apply_url = job_url

    try:
        logger.info(f"[page_capturer] navigating to job page | url={job_url}")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        # Try to find the apply link without clicking
        for selector in APPLY_LINK_SELECTORS:
            try:
                link = page.locator(selector).first
                if await link.count():
                    href = await link.get_attribute("href")
                    if href and href.startswith("http"):
                        apply_url = href
                        logger.info(f"[page_capturer] found apply link | url={apply_url}")
                        break
            except Exception:
                continue

        # Navigate to the actual apply page
        if apply_url != job_url:
            logger.info(f"[page_capturer] navigating to apply page | url={apply_url}")
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

        # Full-page screenshot
        full_path = os.path.join(screenshots_dir, f"form_full_{app_id}_{ts}.png")
        await page.screenshot(path=full_path, full_page=True)
        screenshots.append(full_path)
        logger.info(f"[page_capturer] full-page screenshot saved | path={full_path}")

        # Viewport scroll screenshots for very tall pages
        viewport_height = await page.evaluate("window.innerHeight")
        scroll_height = await page.evaluate("document.body.scrollHeight")

        if scroll_height > 3 * viewport_height:
            logger.info(f"[page_capturer] tall page ({scroll_height}px), taking scroll screenshots")
            positions = [0, scroll_height // 2, max(0, scroll_height - viewport_height)]
            for i, pos in enumerate(positions):
                await page.evaluate(f"window.scrollTo(0, {pos})")
                await asyncio.sleep(0.8)
                scroll_path = os.path.join(screenshots_dir, f"form_scroll{i}_{app_id}_{ts}.png")
                await page.screenshot(path=scroll_path)
                screenshots.append(scroll_path)

    except Exception as e:
        logger.error(f"[page_capturer] error | {e}")

    return {"screenshots": screenshots, "apply_url": apply_url}
