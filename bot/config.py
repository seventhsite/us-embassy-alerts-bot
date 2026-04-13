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

# Proxy URL for RSS requests (required for datacenter IPs blocked by CloudFront)
# Supports HTTP, HTTPS, SOCKS4, SOCKS5 proxies
# Examples:
#   http://user:pass@proxy.example.com:8080
#   socks5://user:pass@proxy.example.com:1080
PROXY_URL: str = os.getenv("PROXY_URL", "")
