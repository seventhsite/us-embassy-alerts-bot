"""Handler package — registers all command and callback handlers."""

from aiogram import Dispatcher

from bot.handlers.latest import router as latest_router
from bot.handlers.my_subs import router as my_subs_router
from bot.handlers.start import router as start_router
from bot.handlers.subscribe import router as subscribe_router
from bot.handlers.unsubscribe import router as unsubscribe_router


def register_all_handlers(dp: Dispatcher) -> None:
    """Register all handler routers with the dispatcher."""
    dp.include_router(start_router)
    dp.include_router(subscribe_router)
    dp.include_router(unsubscribe_router)
    dp.include_router(my_subs_router)
    dp.include_router(latest_router)
