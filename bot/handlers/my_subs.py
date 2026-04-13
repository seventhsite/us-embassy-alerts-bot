"""Handler for /my command — show user's active subscriptions."""

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from bot import database as db
from bot.countries import ALL_COUNTRIES
from bot.i18n import t

router = Router(name="my_subs")


@router.message(Command("my"))
async def cmd_my_subscriptions(message: Message) -> None:
    """Handle /my — list the user's active subscriptions."""
    user_id = message.from_user.id if message.from_user else 0
    subs = await db.get_user_subscriptions(user_id)

    if not subs:
        await message.answer(
            t("no_subscriptions"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Build formatted list
    lines: list[str] = []
    for code in subs:
        country = ALL_COUNTRIES.get(code)
        if country:
            lines.append(f"  {country.flag} {country.name}")
        else:
            lines.append(f"  🏳️ {code}")

    await message.answer(
        t("my_subscriptions", count=len(subs), list="\n".join(lines)),
        parse_mode=ParseMode.MARKDOWN,
    )
