from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from telegram_with_max import InlineButton, InlineKeyboard, Platform
from telegram_with_max.events import (
    MaxCallback,
    MaxMessage,
    TelegramCallback,
    TelegramMessage,
)


def telegram_message_raw():
    return SimpleNamespace(
        from_user=SimpleNamespace(
            id=10,
            full_name="Telegram User",
            username="tg_user",
        ),
        chat=SimpleNamespace(id=20),
        text="hello",
        answer=AsyncMock(return_value="answered"),
        reply=AsyncMock(return_value="replied"),
        edit_text=AsyncMock(return_value="edited"),
        delete=AsyncMock(return_value="deleted"),
    )


@pytest.mark.asyncio
async def test_telegram_message_exposes_common_fields_and_methods():
    raw = telegram_message_raw()
    message = TelegramMessage(raw)
    keyboard = InlineKeyboard([[InlineButton("OK", "ok")]])

    assert message.platform is Platform.TELEGRAM
    assert (message.user_id, message.chat_id, message.text) == (10, 20, "hello")
    assert (message.display_name, message.username) == (
        "Telegram User",
        "tg_user",
    )
    assert await message.answer("answer", reply_markup=keyboard) == "answered"
    assert await message.reply("reply") == "replied"
    assert await message.edit_text("edit") == "edited"
    assert await message.delete() == "deleted"
    markup = raw.answer.await_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].text == "OK"


@pytest.mark.asyncio
async def test_max_message_exposes_common_fields_and_methods():
    native_message = SimpleNamespace(
        body=SimpleNamespace(text="hello max"),
        sender=SimpleNamespace(full_name="MAX User", username="max_user"),
        answer=AsyncMock(return_value="answered"),
        reply=AsyncMock(return_value="replied"),
        edit=AsyncMock(return_value="edited"),
        delete=AsyncMock(return_value="deleted"),
    )
    event = SimpleNamespace(message=native_message, get_ids=lambda: (30, 40))
    message = MaxMessage(event)

    assert message.platform is Platform.MAX
    assert (message.user_id, message.chat_id, message.text) == (40, 30, "hello max")
    assert (message.display_name, message.username) == ("MAX User", "max_user")
    assert await message.answer("answer") == "answered"
    assert await message.reply("reply") == "replied"
    assert await message.edit_text("edit") == "edited"
    assert await message.delete() == "deleted"


@pytest.mark.asyncio
async def test_callbacks_use_platform_specific_acknowledgements():
    tg_raw = SimpleNamespace(
        from_user=SimpleNamespace(id=10),
        data="demo:tg",
        message=telegram_message_raw(),
        answer=AsyncMock(return_value="tg-ack"),
    )
    tg_callback = TelegramCallback(tg_raw)
    assert await tg_callback.answer("done") == "tg-ack"
    tg_raw.answer.assert_awaited_once_with(text="done")

    max_native_message = SimpleNamespace(body=SimpleNamespace(text="button"))
    max_raw = SimpleNamespace(
        callback=SimpleNamespace(payload="demo:max"),
        message=max_native_message,
        get_ids=lambda: (30, 40),
        answer=AsyncMock(return_value="max-ack"),
    )
    max_callback = MaxCallback(max_raw)
    assert await max_callback.answer("done") == "max-ack"
    max_raw.answer.assert_awaited_once_with(notification="done")
