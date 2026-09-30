from __future__ import annotations

import asyncio
from contextlib import suppress

from aiogram import Bot as TelegramBot
from aiogram import Dispatcher as TelegramDispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode as TelegramParseMode
from maxapi import Bot as MaxBot
from maxapi import Dispatcher as MaxDispatcher
from maxapi.enums import TextFormat as MaxTextFormat

from .keyboards import InlineKeyboard, to_max_attachments, to_telegram_markup
from .platform import Platform
from .router import Router


class App:
    """Owns and runs Telegram and MAX polling runtimes."""

    def __init__(
        self, *, telegram_token: str, max_token: str,
        telegram_proxy: str | None = None,
    ) -> None:
        self.telegram_bot = TelegramBot(
            token=telegram_token,
            session=AiohttpSession(proxy=telegram_proxy),
            default=DefaultBotProperties(parse_mode=TelegramParseMode.HTML),
        )
        self.max_bot = MaxBot(token=max_token, format=MaxTextFormat.HTML)
        self.telegram_dispatcher = TelegramDispatcher()
        self.max_dispatcher = MaxDispatcher()
        self._routers: set[int] = set()

    def include_router(self, router: Router) -> None:
        router_id = id(router)
        if router_id in self._routers:
            raise ValueError("Router is already included")
        self.telegram_dispatcher.include_router(router.telegram)
        self.max_dispatcher.include_routers(router.max)
        self._routers.add(router_id)

    async def send_message(
        self,
        *,
        platform: Platform,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboard | None = None,
        **kwargs: object,
    ) -> object:
        """Send a message without exposing a platform-specific bot client."""
        if platform is Platform.TELEGRAM:
            return await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=to_telegram_markup(reply_markup),
                **kwargs,
            )
        if platform is Platform.MAX:
            return await self.max_bot.send_message(
                chat_id=chat_id,
                text=text,
                attachments=to_max_attachments(reply_markup),
                **kwargs,
            )
        raise ValueError(f"Unsupported platform: {platform!r}")

    async def _ensure_max_polling_available(self) -> None:
        subscriptions = await self.max_bot.get_subscriptions()
        if subscriptions.subscriptions:
            urls = ", ".join(item.url for item in subscriptions.subscriptions)
            raise RuntimeError(
                "MAX polling cannot start while webhook subscriptions are active: "
                f"{urls}"
            )

    async def run_polling(self) -> None:
        try:
            await self._ensure_max_polling_available()
        except Exception:
            await self.close()
            raise
        tasks = [
            asyncio.create_task(
                self.telegram_dispatcher.start_polling(self.telegram_bot),
                name="telegram-polling",
            ),
            asyncio.create_task(
                self.max_dispatcher.start_polling(self.max_bot),
                name="max-polling",
            ),
        ]
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.close()

    async def close(self) -> None:
        with suppress(Exception):
            await self.telegram_bot.session.close()
        with suppress(Exception):
            await self.max_bot.close_session()
