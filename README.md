# 🇺🇸 US Embassy Alert Bot

A Telegram bot that monitors U.S. Embassy security alerts worldwide and notifies subscribers about new alerts in real-time.

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

- Docker & Docker Compose
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/usembassy-notify.git
   cd usembassy-notify
   ```

2. Create the `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and set your TELEGRAM_BOT_TOKEN
   ```

3. Create the data directory:
   ```bash
   mkdir -p data
   ```

4. Build and run:
   ```bash
   docker compose up -d --build
   ```

5. Check logs:
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

## Adding a New Language

1. Copy the English locale file:
   ```bash
   cp bot/locales/en.json bot/locales/ru.json
   ```

2. Translate all values in the new file (keep the keys unchanged).

3. Commit and redeploy:
   ```bash
   git add bot/locales/ru.json
   git commit -m "Add Russian locale"
   docker compose up -d --build
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

## License

MIT
