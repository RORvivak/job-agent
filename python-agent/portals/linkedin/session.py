import os
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


SESSIONS_DIR = Path(__file__).parent.parent.parent / ".sessions" / "linkedin"


async def get_context(playwright, user_id: int) -> tuple[Browser, BrowserContext, Page]:
    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
    browser = await playwright.chromium.launch(headless=headless)
    session_path = SESSIONS_DIR / f"{user_id}.json"

    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"

    if session_path.exists():
        context = await browser.new_context(storage_state=str(session_path), user_agent=user_agent)
    else:
        context = await browser.new_context(user_agent=user_agent)

    page = await context.new_page()
    return browser, context, page


async def save_session(context: BrowserContext, user_id: int) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_path = SESSIONS_DIR / f"{user_id}.json"
    await context.storage_state(path=str(session_path))


async def is_logged_in(page: Page) -> bool:
    try:
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
        # Must be on feed URL AND have the nav bar present (only exists when logged in)
        return "linkedin.com/feed" in page.url
    except Exception:
        return False
