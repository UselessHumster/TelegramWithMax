from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .keyboards import InlineKeyboard, to_max_attachments, to_telegram_markup
from .platform import Platform


class UnifiedMessage(ABC):
    """A platform-neutral incoming message."""

    platform: Platform

    def __init__(
        self,
        *,
        user_id: int,
        chat_id: int,
        text: str | None,
        raw: Any,
    ) -> None:
        self.user_id = user_id
        self.chat_id = chat_id
        self.text = text
        self.raw = raw

    @property
    def is_private(self) -> bool:
        return self.user_id == self.chat_id

    @abstractmethod
    async def answer(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any: ...

    @abstractmethod
    async def reply(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any: ...

    @abstractmethod
    async def edit_text(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any: ...

    @abstractmethod
    async def delete(self) -> Any: ...


class TelegramMessage(UnifiedMessage):
    platform = Platform.TELEGRAM

    def __init__(self, message: Any) -> None:
        super().__init__(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            text=message.text,
            raw=message,
        )

    async def answer(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.raw.answer(
            text,
            reply_markup=to_telegram_markup(reply_markup),
            **kwargs,
        )

    async def reply(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.raw.reply(
            text,
            reply_markup=to_telegram_markup(reply_markup),
            **kwargs,
        )

    async def edit_text(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.raw.edit_text(
            text,
            reply_markup=to_telegram_markup(reply_markup),
            **kwargs,
        )

    async def delete(self) -> Any:
        return await self.raw.delete()


class MaxMessage(UnifiedMessage):
    platform = Platform.MAX

    def __init__(
        self,
        event_or_message: Any,
        *,
        user_id: int | None = None,
        chat_id: int | None = None,
        raw: Any | None = None,
    ) -> None:
        if hasattr(event_or_message, "message"):
            event = event_or_message
            message = event.message
            resolved_chat_id, resolved_user_id = event.get_ids()
            raw = event
        else:
            message = event_or_message
            resolved_user_id = user_id
            resolved_chat_id = chat_id

        if resolved_user_id is None or resolved_chat_id is None:
            raise ValueError("MAX message requires user_id and chat_id")

        body = getattr(message, "body", None)
        super().__init__(
            user_id=resolved_user_id,
            chat_id=resolved_chat_id,
            text=getattr(body, "text", None),
            raw=raw if raw is not None else message,
        )
        self.message = message

    async def answer(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.message.answer(
            text,
            attachments=to_max_attachments(reply_markup),
            **kwargs,
        )

    async def reply(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.message.reply(
            text,
            attachments=to_max_attachments(reply_markup),
            **kwargs,
        )

    async def edit_text(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.message.edit(
            text,
            attachments=to_max_attachments(reply_markup),
            **kwargs,
        )

    async def delete(self) -> Any:
        return await self.message.delete()


class UnifiedCallback(ABC):
    platform: Platform

    def __init__(
        self,
        *,
        user_id: int,
        data: str | None,
        message: UnifiedMessage,
        raw: Any,
    ) -> None:
        self.user_id = user_id
        self.data = data
        self.message = message
        self.raw = raw

    @abstractmethod
    async def answer(self, text: str | None = None, **kwargs: Any) -> Any: ...


class TelegramCallback(UnifiedCallback):
    platform = Platform.TELEGRAM

    def __init__(self, callback: Any) -> None:
        if callback.message is None:
            raise ValueError("Inline Telegram callbacks are not supported")
        super().__init__(
            user_id=callback.from_user.id,
            data=callback.data,
            message=TelegramMessage(callback.message),
            raw=callback,
        )

    async def answer(self, text: str | None = None, **kwargs: Any) -> Any:
        return await self.raw.answer(text=text, **kwargs)


class MaxCallback(UnifiedCallback):
    platform = Platform.MAX

    def __init__(self, callback: Any) -> None:
        chat_id, user_id = callback.get_ids()
        if callback.message is None:
            raise ValueError("MAX callback has no associated message")
        super().__init__(
            user_id=user_id,
            data=callback.callback.payload,
            message=MaxMessage(
                callback.message,
                user_id=user_id,
                chat_id=chat_id,
                raw=callback,
            ),
            raw=callback,
        )

    async def answer(self, text: str | None = None, **kwargs: Any) -> Any:
        return await self.raw.answer(notification=text, **kwargs)
