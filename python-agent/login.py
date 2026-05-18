"""
Run this once to log in to LinkedIn and save the session.
After this, the agent will reuse the session automatically.

Usage:
    .venv/bin/python login.py
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSIONS_DIR = Path(__file__).parent / ".sessions" / "linkedin"
USER_ID = 1


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")

        print(">>> Log in to LinkedIn in the browser window.")
        print(">>> Once you see your feed, come back here and press Enter.")
        input()

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_path = SESSIONS_DIR / f"{USER_ID}.json"
        await context.storage_state(path=str(session_path))
        print(f"Session saved to {session_path}")
        await browser.close()


asyncio.run(main())
