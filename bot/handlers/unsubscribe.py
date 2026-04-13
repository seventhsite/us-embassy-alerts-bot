"""Handler for /unsubscribe command with inline keyboard."""

import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import database as db
from bot.countries import ALL_COUNTRIES
from bot.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="unsubscribe")

CB_UNSUB = "unsub:"  # unsub:<country_code>


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message) -> None:
    """Handle /unsubscribe — show user's subscriptions to choose from."""
    user_id = message.from_user.id if message.from_user else 0
    subs = await db.get_user_subscriptions(user_id)

    if not subs:
        await message.answer(
            t("no_subscriptions"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Build keyboard with current subscriptions
    rows: list[list[InlineKeyboardButton]] = []
    for code in subs:
        country = ALL_COUNTRIES.get(code)
        if country:
            rows.append(
                [InlineKeyboardButton(
                    text=f"{country.flag} {country.name}",
                    callback_data=f"{CB_UNSUB}{code}",
                )]
            )

    await message.answer(
        t("choose_unsub_country"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data.startswith(CB_UNSUB))
async def cb_unsubscribe(callback: CallbackQuery) -> None:
    """Handle unsubscribe button — remove the subscription."""
    code = callback.data.removeprefix(CB_UNSUB)
    user_id = callback.from_user.id
    country = ALL_COUNTRIES.get(code)

    if not country:
        await callback.answer(t("error_generic"), show_alert=True)
        return

    removed = await db.remove_subscription(user_id, code)

    if removed:
        await callback.message.edit_text(
            t("unsubscribed", country=country.name, flag=country.flag),
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("User %d unsubscribed from %s", user_id, code)
    else:
        await callback.message.edit_text(
            t("not_subscribed", country=country.name, flag=country.flag),
            parse_mode=ParseMode.MARKDOWN,
        )

    await callback.answer()
