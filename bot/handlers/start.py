"""Handlers for /start and /help commands."""

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from bot import database as db
from bot.config import MAX_FREE_SUBS
from bot.i18n import t

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle the /start command — greet the user and show help."""
    if message.from_user:
        await db.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

    await message.answer(
        t("welcome"),
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle the /help command — show available commands."""
    await message.answer(
        t("help", max_free=MAX_FREE_SUBS),
        parse_mode=ParseMode.MARKDOWN,
    )
