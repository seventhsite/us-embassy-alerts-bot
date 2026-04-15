"""
Browser manager for Playwright.

Provides a shared headless Chromium instance for fetching RSS feeds.
The browser is launched once and reused across all requests.
"""

import logging

from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)

_playwright = None
_browser: Browser | None = None


async def get_browser() -> Browser:
    """Get or launch the shared browser instance."""
    global _playwright, _browser

    if _browser is None or not _browser.is_connected():
        logger.info("Launching headless Chromium...")
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ],
        )
        logger.info("Chromium browser launched")

    return _browser


async def close_browser() -> None:
    """Close the shared browser instance."""
    global _playwright, _browser

    if _browser:
        await _browser.close()
        _browser = None
        logger.info("Browser closed")

    if _playwright:
        await _playwright.stop()
        _playwright = None
