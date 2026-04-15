"""
Main entry point for the US Embassy Alert Notification Bot.

Initializes the bot, registers handlers, starts the RSS polling loop,
and runs the aiogram dispatcher.
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot import database as db
from bot.config import BOT_TOKEN, DB_PATH, LOG_LEVEL
from bot.handlers import register_all_handlers
from bot.i18n import load_locales
from bot.scheduler import run_polling_loop


def _setup_logging() -> None:
    """Configure logging with a readable format."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Reduce noise from third-party libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)


async def on_startup(bot: Bot) -> None:
    """Actions to perform when the bot starts."""
    me = await bot.get_me()
    logging.getLogger(__name__).info(
        "Bot started: @%s (%s)", me.username, me.full_name
    )


async def on_shutdown(bot: Bot) -> None:
    """Actions to perform when the bot shuts down."""
    from bot.browser import close_browser
    await close_browser()
    await db.close_db()
    logging.getLogger(__name__).info("Bot stopped")


async def main() -> None:
    """Main async entry point."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)


    # Ensure data directory exists
    db_dir = os.path.dirname(DB_PATH) or "."
    os.makedirs(db_dir, exist_ok=True)

    # Load translations
    load_locales()

    # Initialize database
    await db.init_db()

    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Register lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register all handlers
    register_all_handlers(dp)

    # Start RSS polling in the background
    polling_task = asyncio.create_task(run_polling_loop(bot))

    try:
        # Start long polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    finally:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
