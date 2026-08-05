import asyncio
from unittest.mock import AsyncMock

import pytest

from telegram_with_max import App, Router


def make_app():
    return App(
        telegram_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        max_token="max-token",
    )


def test_app_includes_native_routers_once():
    app = make_app()
    router = Router()

    app.include_router(router)

    assert router.telegram.parent_router is app.telegram_dispatcher
    assert router.max in app.max_dispatcher.routers
    with pytest.raises(ValueError, match="already included"):
        app.include_router(router)


@pytest.mark.asyncio
async def test_polling_closes_both_sessions_when_one_runtime_finishes():
    app = make_app()
    app.telegram_dispatcher.start_polling = AsyncMock(return_value=None)

    max_started = asyncio.Event()

    async def max_polling(bot):
        max_started.set()
        await asyncio.Event().wait()

    app.max_dispatcher.start_polling = max_polling
    app.telegram_bot.session.close = AsyncMock()
    app.max_bot.close_session = AsyncMock()

    await app.run_polling()

    assert max_started.is_set()
    app.telegram_bot.session.close.assert_awaited_once()
    app.max_bot.close_session.assert_awaited_once()
