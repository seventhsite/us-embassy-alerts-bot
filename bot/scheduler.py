"""
Periodic RSS polling scheduler.

Distributes polling across the configured interval so not all countries
are checked simultaneously. Sends new alerts to subscribers.
"""

import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import URLInputFile

from bot import database as db
from bot.config import POLL_INTERVAL
from bot.countries import ALL_COUNTRIES
from bot.i18n import t
from bot.rss_fetcher import AlertItem, fetch_alerts

logger = logging.getLogger(__name__)


def _format_alert_message(item: AlertItem, country_name: str, flag: str) -> str:
    """Format an alert item into a Telegram message with Markdown."""
    parts: list[str] = []

    # Title line
    parts.append(t("alert_title", country=country_name, flag=flag))

    # Alert title (bold)
    safe_title = _escape_md(item.title)
    parts.append(f"*{safe_title}*\n")

    # Publication date
    if item.pub_date:
        parts.append(t("alert_date", date=_escape_md(item.pub_date)))

    # Body / description
    if item.description:
        parts.append(_escape_md(item.description))

    # Link
    if item.link:
        parts.append(t("alert_link", link=item.link))

    return "".join(parts)


def _escape_md(text: str) -> str:
    """Escape special Markdown characters for Telegram MarkdownV2-safe display."""
    # For regular Markdown (not V2), we only need to escape a few characters
    # that could break formatting when they appear in user content
    for char in ("*", "_", "`", "["):
        text = text.replace(char, "\\" + char)
    return text


async def _send_alert_to_user(
    bot: Bot, user_id: int, item: AlertItem, country_name: str, flag: str
) -> None:
    """Send a single alert notification to a user."""
    text = _format_alert_message(item, country_name, flag)

    try:
        if item.image_url:
            # Send as photo with caption
            try:
                photo = URLInputFile(item.image_url)
                # Telegram caption limit is 1024 characters
                caption = text[:1024] if len(text) > 1024 else text
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            except Exception as photo_err:
                logger.warning(
                    "Failed to send photo to %d: %s, falling back to text",
                    user_id,
                    photo_err,
                )

        # Send as text message
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False,
        )

    except Exception as exc:
        logger.error("Failed to send alert to user %d: %s", user_id, exc)


async def poll_country(
    bot: Bot,
    country_code: str,
) -> int:
    """
    Poll a single country's RSS feed and notify subscribers of new alerts.

    Returns the number of new alerts found.
    """
    country = ALL_COUNTRIES.get(country_code)
    if not country:
        logger.warning("Unknown country code: %s", country_code)
        return 0

    items = await fetch_alerts(country_code, country.feed_url)
    if not items:
        return 0

    new_count = 0
    subscribers = await db.get_subscribers_for_country(country_code)

    if not subscribers:
        # No subscribers — still mark alerts as seen to avoid flood on resubscribe
        for item in items:
            await db.mark_alert_seen(
                country_code, item.guid, item.title, item.link, item.pub_date
            )
        return 0

    for item in items:
        is_new = await db.mark_alert_seen(
            country_code, item.guid, item.title, item.link, item.pub_date
        )
        if is_new:
            new_count += 1
            logger.info("New alert for %s: %s", country_code, item.title)

            # Notify all subscribers
            for user_id in subscribers:
                await _send_alert_to_user(
                    bot, user_id, item, country.name, country.flag
                )
                # Small delay between messages to respect Telegram rate limits
                await asyncio.sleep(0.1)

    return new_count


async def run_polling_loop(bot: Bot) -> None:
    """
    Main polling loop that runs forever.

    Distributes country polls evenly across the configured interval
    so the traffic is spread out, not bursting all at once.
    """
    logger.info(
        "Starting RSS polling loop (interval: %d seconds)", POLL_INTERVAL
    )

    while True:
        try:
            # Get only countries with active subscriptions
            countries = await db.get_all_subscribed_countries()

            if not countries:
                logger.debug("No subscribed countries, sleeping for %ds", POLL_INTERVAL)
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # Calculate delay between each country poll to spread over the interval
            delay_between = POLL_INTERVAL / len(countries) if len(countries) > 1 else 0

            logger.info(
                "Polling %d countries (%.1fs between each)",
                len(countries),
                delay_between,
            )

            for i, code in enumerate(countries):
                try:
                    new_count = await poll_country(bot, code)
                    if new_count:
                        logger.info(
                            "Found %d new alert(s) for %s", new_count, code
                        )
                except Exception as exc:
                    logger.error("Error polling %s: %s", code, exc)

                # Wait before polling next country (staggered approach)
                if i < len(countries) - 1 and delay_between > 0:
                    await asyncio.sleep(delay_between)

            # Periodic cleanup of old seen alerts (every cycle)
            try:
                removed = await db.cleanup_old_alerts(days=90)
                if removed:
                    logger.info("Cleaned up %d old alert records", removed)
            except Exception as exc:
                logger.error("Error during alert cleanup: %s", exc)

        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
            raise
        except Exception as exc:
            logger.error("Unexpected error in polling loop: %s", exc)
            await asyncio.sleep(60)  # Wait before retrying on unexpected errors
