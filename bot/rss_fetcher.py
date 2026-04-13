"""
RSS feed fetcher with retry logic and CloudFront-friendly headers.

Fetches and parses RSS 2.0 feeds from U.S. Embassy websites.
"""

import asyncio
import html
import logging
import random
import re
from dataclasses import dataclass

import aiohttp
import feedparser

from bot.config import DEFAULT_HEADERS, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENTS

logger = logging.getLogger(__name__)

# Maximum length for the alert body text sent in Telegram messages
MAX_BODY_LENGTH = 800


@dataclass
class AlertItem:
    """A parsed alert from an RSS feed."""

    guid: str
    title: str
    link: str
    pub_date: str
    description: str  # Clean text summary
    image_url: str | None  # Thumbnail / enclosure image URL


def _strip_html(raw_html: str) -> str:
    """Remove HTML tags and decode entities, returning plain text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", raw_html)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_image_url(entry: dict) -> str | None:
    """
    Extract the best available image URL from an RSS entry.

    Priority: enclosure -> media:content -> media:thumbnail -> <img> in content.
    """
    # 1. Enclosure
    enclosures = entry.get("enclosures", [])
    for enc in enclosures:
        url = enc.get("href") or enc.get("url", "")
        if url and ("image" in enc.get("type", "") or _looks_like_image(url)):
            return url

    # 2. media:content
    media = entry.get("media_content", [])
    for m in media:
        url = m.get("url", "")
        if url and _looks_like_image(url):
            return url

    # 3. media:thumbnail
    thumbnails = entry.get("media_thumbnail", [])
    for th in thumbnails:
        url = th.get("url", "")
        if url:
            return url

    # 4. First <img> in content:encoded or description
    for field in ("content", "summary"):
        content = entry.get(field, "")
        if isinstance(content, list):
            content = content[0].get("value", "") if content else ""
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(content))
        if match:
            url = match.group(1)
            if _looks_like_image(url):
                return url

    return None


def _looks_like_image(url: str) -> bool:
    """Check if a URL looks like an image resource."""
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"))


def _get_best_content(entry: dict) -> str:
    """
    Extract the best content text from an RSS entry.

    Prefers content:encoded over description, and strips HTML.
    """
    # content:encoded (full post body)
    content_list = entry.get("content", [])
    if content_list and isinstance(content_list, list):
        raw = content_list[0].get("value", "")
        if raw:
            return _strip_html(raw)

    # description / summary
    summary = entry.get("summary", "")
    if summary:
        return _strip_html(summary)

    return ""


def _parse_feed(raw_xml: str, country_code: str) -> list[AlertItem]:
    """Parse raw XML into a list of AlertItem objects."""
    feed = feedparser.parse(raw_xml)

    if feed.bozo and not feed.entries:
        logger.warning(
            "Feed parse error for %s: %s", country_code, feed.bozo_exception
        )
        return []

    items: list[AlertItem] = []
    for entry in feed.entries:
        guid = entry.get("id", entry.get("link", ""))
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        pub_date = entry.get("published", "")
        body = _get_best_content(entry)
        image_url = _extract_image_url(entry)

        # Truncate long body text
        if len(body) > MAX_BODY_LENGTH:
            body = body[:MAX_BODY_LENGTH].rsplit(" ", 1)[0] + "…"

        items.append(
            AlertItem(
                guid=guid,
                title=title,
                link=link,
                pub_date=pub_date,
                description=body,
                image_url=image_url,
            )
        )

    return items


async def fetch_alerts(
    country_code: str,
    feed_url: str,
    session: aiohttp.ClientSession | None = None,
) -> list[AlertItem]:
    """
    Fetch and parse alerts from a country's RSS feed.

    Includes retry logic with exponential backoff and UA rotation.
    """
    own_session = session is None
    if own_session:
        session = aiohttp.ClientSession()

    try:
        for attempt in range(1, MAX_RETRIES + 1):
            headers = {
                **DEFAULT_HEADERS,
                "User-Agent": random.choice(USER_AGENTS),
            }
            try:
                async with session.get(
                    feed_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    ssl=True,
                ) as resp:
                    if resp.status == 200:
                        raw = await resp.text()
                        items = _parse_feed(raw, country_code)
                        logger.debug(
                            "Fetched %d alerts for %s", len(items), country_code
                        )
                        return items

                    logger.warning(
                        "HTTP %d for %s (attempt %d/%d)",
                        resp.status,
                        country_code,
                        attempt,
                        MAX_RETRIES,
                    )

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(
                    "Request error for %s (attempt %d/%d): %s",
                    country_code,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )

            # Exponential backoff with jitter
            if attempt < MAX_RETRIES:
                delay = (2**attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)

        logger.error("All %d attempts failed for %s", MAX_RETRIES, country_code)
        return []

    finally:
        if own_session:
            await session.close()
