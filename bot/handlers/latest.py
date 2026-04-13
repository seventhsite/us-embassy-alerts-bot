"""
Handler for /latest command — fetch and display recent alerts on demand.

Usage: /latest Serbia  |  /latest rs  |  /latest germany
"""

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, URLInputFile

from bot import database as db
from bot.countries import ALL_COUNTRIES, find_country_by_name
from bot.i18n import t
from bot.rss_fetcher import fetch_alerts

logger = logging.getLogger(__name__)
router = Router(name="latest")

# Number of alerts to show
LATEST_COUNT = 3


@router.message(Command("latest"))
async def cmd_latest(message: Message) -> None:
    """
    Handle /latest <country> — fetch recent alerts for a country.

    Works without requiring a subscription.
    """
    # Extract country name from the command arguments
    raw_text = message.text or ""
    parts = raw_text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            t("latest_no_country"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    query = parts[1].strip()
    country = find_country_by_name(query)

    if not country:
        await message.answer(
            t("latest_country_not_found", query=query),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # First check if we have cached alerts in the database
    cached = await db.get_recent_alerts(country.code, limit=LATEST_COUNT)

    if cached:
        # Show cached alerts
        text = t("latest_header", country=country.name, flag=country.flag)
        for a in cached:
            title = a.get("title") or "No title"
            link = a.get("link") or ""
            pub_date = a.get("pub_date") or ""

            text += f"\n• *{title}*"
            if pub_date:
                text += f"\n  📅 {pub_date}"
            if link:
                text += f"\n  🔗 [Read more]({link})"
            text += "\n"

        await message.answer(text, parse_mode=ParseMode.MARKDOWN)
        return

    # No cached alerts — fetch fresh from RSS
    status_msg = await message.answer("⏳ Fetching alerts...")

    items = await fetch_alerts(country.code, country.feed_url)

    if not items:
        await status_msg.edit_text(
            t("latest_no_alerts", country=country.name, flag=country.flag),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Mark all fetched alerts as seen (for future reference)
    for item in items:
        await db.mark_alert_seen(
            country.code, item.guid, item.title, item.link, item.pub_date
        )

    # Show only the first LATEST_COUNT
    display_items = items[:LATEST_COUNT]

    # Delete the status message
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Send each alert as a separate message
    for item in display_items:
        text_parts = [
            t("alert_title", country=country.name, flag=country.flag),
            f"*{item.title}*\n",
        ]

        if item.pub_date:
            text_parts.append(t("alert_date", date=item.pub_date))

        if item.description:
            text_parts.append(item.description)

        if item.link:
            text_parts.append(t("alert_link", link=item.link))

        text = "".join(text_parts)

        try:
            if item.image_url:
                try:
                    photo = URLInputFile(item.image_url)
                    caption = text[:1024] if len(text) > 1024 else text
                    await message.answer_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    continue
                except Exception:
                    pass  # Fall back to text

            await message.answer(
                text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
        except Exception as exc:
            logger.error("Error sending latest alert: %s", exc)

    logger.info(
        "Showed %d latest alerts for %s to user %d",
        len(display_items),
        country.code,
        message.from_user.id if message.from_user else 0,
    )
