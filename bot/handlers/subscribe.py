"""
Handlers for /subscribe command with inline keyboard navigation.

Flow: /subscribe -> Choose Region -> Choose Country (paginated) -> Confirm
"""

import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import database as db
from bot.config import MAX_FREE_SUBS
from bot.countries import ALL_COUNTRIES, REGIONS, get_region_names
from bot.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="subscribe")

# Number of country buttons per page
COUNTRIES_PER_PAGE = 8

# Callback data prefixes
CB_REGION = "sub_region:"      # sub_region:<region_name>
CB_COUNTRY = "sub_country:"    # sub_country:<country_code>
CB_PAGE = "sub_page:"          # sub_page:<region_name>:<page>


def _build_region_keyboard() -> InlineKeyboardMarkup:
    """Build the region selection keyboard."""
    buttons = []
    for region_name in get_region_names():
        buttons.append(
            [InlineKeyboardButton(
                text=region_name,
                callback_data=f"{CB_REGION}{region_name}",
            )]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_country_keyboard(region_name: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build a paginated country selection keyboard for a region."""
    countries = REGIONS.get(region_name, [])
    total_pages = max(1, (len(countries) + COUNTRIES_PER_PAGE - 1) // COUNTRIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * COUNTRIES_PER_PAGE
    end = start + COUNTRIES_PER_PAGE
    page_countries = countries[start:end]

    # Country buttons (2 columns)
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(page_countries), 2):
        row = []
        for c in page_countries[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{c.flag} {c.name}",
                    callback_data=f"{CB_COUNTRY}{c.code}",
                )
            )
        rows.append(row)

    # Navigation row
    nav_row: list[InlineKeyboardButton] = []

    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text=t("prev_button"),
                callback_data=f"{CB_PAGE}{region_name}:{page - 1}",
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            text=t("page_info", current=page + 1, total=total_pages),
            callback_data="noop",
        )
    )

    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text=t("next_button"),
                callback_data=f"{CB_PAGE}{region_name}:{page + 1}",
            )
        )

    rows.append(nav_row)

    # Back button
    rows.append(
        [InlineKeyboardButton(
            text=t("back_button"),
            callback_data="sub_back_regions",
        )]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    """Handle /subscribe — show region selection keyboard."""
    if message.from_user:
        await db.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

    await message.answer(
        t("choose_region"),
        reply_markup=_build_region_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data.startswith(CB_REGION))
async def cb_region_selected(callback: CallbackQuery) -> None:
    """Handle region selection — show countries in that region."""
    region_name = callback.data.removeprefix(CB_REGION)

    await callback.message.edit_text(
        t("choose_country", region=region_name),
        reply_markup=_build_country_keyboard(region_name, page=0),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_PAGE))
async def cb_page_navigate(callback: CallbackQuery) -> None:
    """Handle pagination — switch to a different page of countries."""
    payload = callback.data.removeprefix(CB_PAGE)
    # payload = "region_name:page_number"
    parts = payload.rsplit(":", 1)
    region_name = parts[0]
    page = int(parts[1]) if len(parts) > 1 else 0

    await callback.message.edit_reply_markup(
        reply_markup=_build_country_keyboard(region_name, page=page),
    )
    await callback.answer()


@router.callback_query(F.data == "sub_back_regions")
async def cb_back_to_regions(callback: CallbackQuery) -> None:
    """Handle back button — return to region selection."""
    await callback.message.edit_text(
        t("choose_region"),
        reply_markup=_build_region_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_COUNTRY))
async def cb_country_selected(callback: CallbackQuery) -> None:
    """Handle country selection — subscribe the user."""
    code = callback.data.removeprefix(CB_COUNTRY)
    country = ALL_COUNTRIES.get(code)
    user_id = callback.from_user.id

    if not country:
        await callback.answer(t("error_generic"), show_alert=True)
        return

    # Check subscription limit
    current_count = await db.get_subscription_count(user_id)
    if current_count >= MAX_FREE_SUBS:
        # Check if already subscribed (allow re-clicking)
        existing = await db.get_user_subscriptions(user_id)
        if code not in existing:
            await callback.message.edit_text(
                t("sub_limit_reached", max_free=MAX_FREE_SUBS),
                parse_mode=ParseMode.MARKDOWN,
            )
            await callback.answer()
            return

    # Attempt to subscribe
    is_new = await db.add_subscription(user_id, code)

    if is_new:
        await callback.message.edit_text(
            t("subscribed", country=country.name, flag=country.flag),
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("User %d subscribed to %s", user_id, code)
    else:
        await callback.message.edit_text(
            t("already_subscribed", country=country.name, flag=country.flag),
            parse_mode=ParseMode.MARKDOWN,
        )

    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    """Handle no-op button presses (e.g., page counter)."""
    await callback.answer()
