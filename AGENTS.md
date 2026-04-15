# AI Agent Instructions

This document provides context for AI coding agents working on this project.

## Project Overview

A Telegram bot that monitors U.S. Embassy security alerts (RSS feeds) across 170+ countries and notifies subscribers in real-time. Built with Python 3.13, aiogram 3.27, and deployed via Docker.

## Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│  Telegram    │◄───►│  Bot (Docker/Hetzner) │────►│  Cloudflare Worker │
│  Bot API     │     │  aiogram + aiohttp    │     │  RSS Proxy         │
└─────────────┘     └──────────┬───────────┘     └────────┬──────────┘
                               │                          │
                               ▼                          ▼
                    ┌──────────────────┐        ┌─────────────────────┐
                    │  SQLite Database  │        │  *.usembassy.gov    │
                    │  /data/bot.db     │        │  (CloudFront WAF)   │
                    └──────────────────┘        └─────────────────────┘
```

### Why the Cloudflare Worker?

U.S. Embassy websites (`*.usembassy.gov`) are behind CloudFront WAF which **blocks all datacenter/hosting IPs** (Hetzner, AWS, GCP, DigitalOcean, etc.) with HTTP 407 responses. This is IP-range based, not TLS-fingerprint based — even headless Chrome (Playwright) and browser-impersonating libraries (curl_cffi) fail from datacenter IPs.

The Cloudflare Worker proxies RSS requests using Cloudflare's anycast IP range, which is not blocked by CloudFront.

**Approaches that were tried and failed:**
- `aiohttp` with browser-like headers → HTTP 407
- `curl_cffi` with Chrome TLS fingerprint impersonation → HTTP 407
- Playwright headless Chromium → `ERR_UNEXPECTED_PROXY_AUTH` (407 interpreted as proxy auth)
- Residential proxy services (proxy-seller, mangoproxy) → Datacenter IPs disguised as residential, still blocked
- Tor → Exit nodes blocked

## Key Components

### Bot (`bot/`)

| File | Purpose |
|------|---------|
| `main.py` | Entry point, bot startup/shutdown lifecycle |
| `config.py` | Environment variables and defaults |
| `database.py` | SQLite via aiosqlite — subscriptions, seen alerts |
| `countries.py` | Registry of 170+ countries with codes, flags, feed URLs |
| `rss_fetcher.py` | Fetches RSS via CF Worker proxy, parses with feedparser |
| `scheduler.py` | Staggered polling loop — distributes requests over interval |
| `i18n.py` | JSON-based localization |
| `handlers/` | Telegram command handlers (start, subscribe, unsubscribe, my, latest) |

### Cloudflare Worker (`cloudflare-worker/`)

| File | Purpose |
|------|---------|
| `src/index.js` | Worker that proxies `GET /?url=<feed_url>` to `*.usembassy.gov` |
| `wrangler.toml` | Wrangler deployment config |

The worker validates an API key via `X-Proxy-Key` header and only allows `*.usembassy.gov` domains.

## Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot API token from @BotFather |
| `RSS_PROXY_URL` | ✅ | Cloudflare Worker URL |
| `RSS_PROXY_KEY` | ✅ | Secret API key for the Worker |
| `POLL_INTERVAL_SECONDS` | ❌ | RSS check interval, default 1800 (30min) |
| `DB_PATH` | ❌ | SQLite path, default `/data/bot.db` |
| `LOG_LEVEL` | ❌ | Logging level, default `INFO` |
| `MAX_FREE_SUBSCRIPTIONS` | ❌ | Per-user limit, default 3 |

## Development

### Local Testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values
python -m bot.main
```

### Docker

```bash
docker compose up -d --build
docker compose logs -f
```

### Deploying the Cloudflare Worker

**Via CLI:**
```bash
cd cloudflare-worker
npm install -g wrangler
wrangler login
wrangler deploy
wrangler secret put PROXY_KEY  # Set the API key
```

**Via Dashboard:** Go to dash.cloudflare.com → Workers & Pages → Create → paste code from `cloudflare-worker/src/index.js`. Add `PROXY_KEY` secret in Settings → Variables and Secrets.

## Deployment

CI/CD is via GitHub Actions (`.github/workflows/deploy.yml`). On push to `main`:
1. Code syncs to `/opt/usembassy-alerts-notify` on the self-hosted runner
2. Docker image is rebuilt
3. Container restarts
4. `.env` and `data/` are preserved across deploys

## Common Issues

### Bot returns "No recent alerts" for all countries
- Check that `RSS_PROXY_URL` and `RSS_PROXY_KEY` are set correctly in `.env`
- Verify the Cloudflare Worker is deployed: `curl -H "X-Proxy-Key: <key>" "<worker_url>/?url=https://rs.usembassy.gov/category/alert/feed/"`
- Check container logs: `docker logs usembassy-alerts-bot`

### CloudFront 407 errors
- This means the request is not going through the Cloudflare Worker
- Verify `RSS_PROXY_URL` is set in `.env`
- The bot should NEVER contact `*.usembassy.gov` directly

### Cloudflare Worker returns 401
- The `X-Proxy-Key` header doesn't match
- Re-check `RSS_PROXY_KEY` in `.env` matches what was set via `wrangler secret put PROXY_KEY`

## Code Conventions

- Async-first: all IO operations use `async/await`
- Type hints on all function signatures
- Docstrings on all public functions
- Logging: use `logging.getLogger(__name__)` per module
- Country codes: ISO 3166-1 alpha-2, lowercase (e.g., `rs`, `de`, `us`)
