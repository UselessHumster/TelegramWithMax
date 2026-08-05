from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InlineButton:
    text: str
    callback_data: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Button text must not be empty")
        if not self.callback_data:
            raise ValueError("Button callback_data must not be empty")


@dataclass(frozen=True, slots=True)
class InlineKeyboard:
    rows: tuple[tuple[InlineButton, ...], ...]

    def __init__(self, rows: Iterable[Iterable[InlineButton]]) -> None:
        normalized = tuple(tuple(row) for row in rows)
        if any(not row for row in normalized):
            raise ValueError("Keyboard rows must not be empty")
        object.__setattr__(self, "rows", normalized)


def to_telegram_markup(keyboard: InlineKeyboard | None):
    if keyboard is None:
        return None

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button.text,
                    callback_data=button.callback_data,
                )
                for button in row
            ]
            for row in keyboard.rows
        ]
    )


def to_max_attachments(keyboard: InlineKeyboard | None):
    if keyboard is None:
        return None

    from maxapi.types.attachments.buttons import CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for row in keyboard.rows:
        builder.row(
            *(
                CallbackButton(text=button.text, payload=button.callback_data)
                for button in row
            )
        )
    return [builder.as_markup()]
