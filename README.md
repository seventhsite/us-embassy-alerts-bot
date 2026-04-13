# 🇺🇸 US Embassy Alert Bot

A Telegram bot that monitors U.S. Embassy security alerts across 170+ countries and notifies subscribers in real-time.

**🤖 Try it now: [@usembassy_notify_bot](https://t.me/usembassy_notify_bot)**

## Features

- 📡 **170+ countries** — Subscribe to alerts from U.S. Embassies across the globe
- 🔔 **Real-time notifications** — Automatic checks every 30 minutes with staggered polling
- 🖼️ **Rich messages** — Alerts include full text, images, and direct links
- 🌍 **Region-based navigation** — Easy country selection via inline keyboards
- 📋 **On-demand queries** — Use `/latest <country>` to check recent alerts without subscribing
- 🌐 **i18n ready** — Add new languages by dropping a JSON file in `bot/locales/`
- 🐳 **Dockerized** — One command to build and run

## Quick Start

### Prerequisites

- Linux server with Docker & Docker Compose
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- GitHub Actions self-hosted runner (for CI/CD)

### Server Preparation

1. Create the deployment directory and set ownership to the runner user:
   ```bash
   sudo mkdir -p /opt/usembassy-alerts-notify
   sudo chown <runner-user>:<runner-user> /opt/usembassy-alerts-notify
   ```

2. Create the `.env` file in the deployment directory:
   ```bash
   cp .env.example /opt/usembassy-alerts-notify/.env
   # Edit .env and set your TELEGRAM_BOT_TOKEN
   ```

3. Create the data directory:
   ```bash
   mkdir -p /opt/usembassy-alerts-notify/data
   ```

### Manual Setup (without CI/CD)

1. Clone the repository:
   ```bash
   git clone https://github.com/seventhsite/us-embassy-alerts-bot.git
   cd us-embassy-alerts-bot
   ```

2. Create the `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and set your TELEGRAM_BOT_TOKEN
   ```

3. Create the data directory and run:
   ```bash
   mkdir -p data
   docker compose up -d --build
   ```

4. Check logs:
   ```bash
   docker compose logs -f bot
   ```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and command overview |
| `/subscribe` | Subscribe to alerts for a country (browseable by region) |
| `/unsubscribe` | Unsubscribe from a country |
| `/my` | View your active subscriptions |
| `/latest <country>` | Get the latest alerts for any country |
| `/help` | Show help message |

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | **Required.** Bot API token |
| `POLL_INTERVAL_SECONDS` | `1800` | RSS check interval (seconds) |
| `DB_PATH` | `/data/bot.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_FREE_SUBSCRIPTIONS` | `3` | Free subscription limit per user |
| `PROXY_URL` | — | Proxy for RSS requests (see below) |

## Proxy Setup

U.S. Embassy websites use CloudFront WAF, which blocks requests from datacenter/hosting IPs (Hetzner, AWS, DigitalOcean, etc.). A **residential or mobile proxy** is required when running the bot on a VPS.

**Supported proxy types:** HTTP, HTTPS, SOCKS4, SOCKS5

```env
# .env examples:
PROXY_URL=http://user:pass@proxy.example.com:8080
PROXY_URL=socks5://user:pass@proxy.example.com:1080
```

**Recommended providers:**
- [Webshare](https://www.webshare.io/) — from ~$3/mo for residential proxies
- [IPRoyal](https://iproyal.com/) — residential proxies with pay-per-GB
- [Bright Data](https://brightdata.com/) — enterprise-grade

> **Note:** Tor (`socks5://127.0.0.1:9050`) is unlikely to work — Tor exit nodes are widely blocked by CloudFront and U.S. government sites.

## Adding a New Language

1. Copy the English locale file:
   ```bash
   cp bot/locales/en.json bot/locales/ru.json
   ```

2. Translate all values in the new file (keep the keys unchanged).

3. Commit and push (auto-deploys via GitHub Actions):
   ```bash
   git add bot/locales/ru.json
   git commit -m "Add Russian locale"
   git push
   ```

## Project Structure

```
usembassy-notify/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py             # Environment configuration
│   ├── database.py           # SQLite layer (aiosqlite)
│   ├── countries.py          # 170+ countries with codes & flags
│   ├── rss_fetcher.py        # RSS parser with retry logic
│   ├── scheduler.py          # Staggered RSS polling loop
│   ├── i18n.py               # Internationalization module
│   ├── locales/
│   │   └── en.json           # English strings
│   └── handlers/
│       ├── __init__.py
│       ├── start.py          # /start, /help
│       ├── subscribe.py      # /subscribe (region → country picker)
│       ├── unsubscribe.py    # /unsubscribe
│       ├── my_subs.py        # /my
│       └── latest.py         # /latest <country>
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD: auto-deploy on push to main
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Tech Stack

- **Python 3.13** — Latest stable Python
- **aiogram 3.27** — Modern async Telegram Bot framework
- **feedparser** — RSS 2.0 parsing
- **aiohttp** — Async HTTP client
- **aiosqlite** — Async SQLite wrapper
- **Docker** — Containerized deployment
- **GitHub Actions** — CI/CD auto-deploy on push

## Deployment (CI/CD)

The project auto-deploys to `/opt/usembassy-alerts-notify` on every push to `main` via a GitHub Actions self-hosted runner.

**What happens on push:**
1. Code is synced to the deployment directory (`.env` and `data/` are preserved)
2. Docker image is rebuilt
3. Container is restarted
4. Health check verifies the container is running

## License

MIT
