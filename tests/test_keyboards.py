from aiogram.types import InlineKeyboardMarkup

from telegram_with_max import InlineButton, InlineKeyboard
from telegram_with_max.keyboards import to_max_attachments, to_telegram_markup


def test_keyboard_is_rendered_for_both_platforms():
    keyboard = InlineKeyboard(
        [
            [InlineButton("One", "one"), InlineButton("Two", "two")],
            [InlineButton("Three", "three")],
        ]
    )

    telegram = to_telegram_markup(keyboard)
    max_attachments = to_max_attachments(keyboard)

    assert isinstance(telegram, InlineKeyboardMarkup)
    assert telegram.inline_keyboard[0][0].callback_data == "one"
    assert len(max_attachments) == 1
    assert max_attachments[0].payload.buttons[0][1].payload == "two"


def test_keyboard_rejects_empty_rows_and_buttons():
    try:
        InlineKeyboard([[]])
    except ValueError as error:
        assert "rows" in str(error)
    else:
        raise AssertionError("empty row was accepted")

    try:
        InlineButton("", "callback")
    except ValueError as error:
        assert "text" in str(error)
    else:
        raise AssertionError("empty button text was accepted")
