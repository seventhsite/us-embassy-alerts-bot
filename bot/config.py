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

# Cloudflare Worker RSS proxy (required)
# The worker proxies requests to *.usembassy.gov bypassing CloudFront WAF.
RSS_PROXY_URL: str = os.getenv("RSS_PROXY_URL", "")
RSS_PROXY_KEY: str = os.getenv("RSS_PROXY_KEY", "")
