"""Application configuration loaded from environment variables."""

import os


# Telegram Bot API token (required)
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# RSS polling interval in seconds (default: 30 minutes)
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL_SECONDS", "1800"))

# SQLite database path
DB_PATH: str = os.getenv("DB_PATH", "/data/bot.db")

# Log level
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Maximum free subscriptions per user
MAX_FREE_SUBS: int = int(os.getenv("MAX_FREE_SUBSCRIPTIONS", "3"))

# HTTP request settings
REQUEST_TIMEOUT: int = 30
MAX_RETRIES: int = 3

# User-Agent strings to rotate (browser-like headers to avoid CloudFront blocks)
USER_AGENTS: list[str] = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) "
        "Gecko/20100101 Firefox/134.0"
    ),
]

# Default HTTP headers sent with RSS requests
DEFAULT_HEADERS: dict[str, str] = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}
