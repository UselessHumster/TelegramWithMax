import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from telegram_with_max import App, InlineButton, InlineKeyboard, Platform, Router


def make_app():
    return App(
        telegram_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        max_token="max-token",
    )


@pytest.mark.asyncio
async def test_telegram_proxy_is_configured():
    app = App(
        telegram_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        max_token="max-token",
        telegram_proxy="http://127.0.0.1:18080",
    )
    assert app.telegram_bot.session.proxy == "http://127.0.0.1:18080"
    await app.close()


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
    app.max_bot.get_subscriptions = AsyncMock(
        return_value=SimpleNamespace(subscriptions=[])
    )
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


@pytest.mark.asyncio
async def test_app_sends_messages_through_selected_platform():
    app = make_app()
    app.telegram_bot.send_message = AsyncMock(return_value="telegram")
    app.max_bot.send_message = AsyncMock(return_value="max")
    keyboard = InlineKeyboard([[InlineButton("OK", "ok")]])

    assert await app.send_message(
        platform=Platform.TELEGRAM,
        chat_id=10,
        text="hello",
        reply_markup=keyboard,
    ) == "telegram"
    assert await app.send_message(
        platform=Platform.MAX,
        chat_id=20,
        text="hello",
        reply_markup=keyboard,
    ) == "max"

    telegram_markup = app.telegram_bot.send_message.await_args_list[0].kwargs[
        "reply_markup"
    ]
    max_attachments = app.max_bot.send_message.await_args_list[0].kwargs[
        "attachments"
    ]
    assert telegram_markup.inline_keyboard[0][0].callback_data == "ok"
    assert max_attachments[0].payload.buttons[0][0].payload == "ok"


@pytest.mark.asyncio
async def test_polling_refuses_active_max_webhook():
    app = make_app()
    app.telegram_bot.session.close = AsyncMock()
    app.max_bot.close_session = AsyncMock()
    app.max_bot.get_subscriptions = AsyncMock(
        return_value=SimpleNamespace(
            subscriptions=[SimpleNamespace(url="https://example.test/max")]
        )
    )

    with pytest.raises(RuntimeError, match="webhook subscriptions"):
        await app.run_polling()

    app.telegram_bot.session.close.assert_awaited_once()
    app.max_bot.close_session.assert_awaited_once()
