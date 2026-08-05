from __future__ import annotations

import asyncio
from contextlib import suppress

from aiogram import Bot as TelegramBot
from aiogram import Dispatcher as TelegramDispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode as TelegramParseMode
from maxapi import Bot as MaxBot
from maxapi import Dispatcher as MaxDispatcher
from maxapi.enums import TextFormat as MaxTextFormat

from .router import Router


class App:
    """Owns and runs Telegram and MAX polling runtimes."""

    def __init__(self, *, telegram_token: str, max_token: str) -> None:
        self.telegram_bot = TelegramBot(
            token=telegram_token,
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

    async def run_polling(self) -> None:
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
