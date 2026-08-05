from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from aiogram import F as TelegramF
from aiogram import Router as TelegramRouter
from aiogram.filters import Command as TelegramCommand
from aiogram.filters import StateFilter as TelegramStateFilter
from aiogram.fsm.context import FSMContext as TelegramFSMContext
from aiogram.types import CallbackQuery as TelegramCallbackQuery
from aiogram.types import Message as TelegramNativeMessage
from maxapi import Router as MaxRouter
from maxapi.context import MemoryContext as MaxMemoryContext
from maxapi.filters import F as MaxF
from maxapi.filters import StateFilter as MaxStateFilter
from maxapi.types import Command as MaxCommand
from maxapi.types import MessageCallback, MessageCreated

from .events import MaxCallback, MaxMessage, TelegramCallback, TelegramMessage
from .fsm import State, UnifiedContext, state_value
from .platform import Platform

Handler = Callable[..., Awaitable[Any]]


def _platforms(value: Iterable[Platform] | None) -> set[Platform]:
    return set(value) if value is not None else set(Platform)


def _state_values(states: Iterable[State | str | None] | State | str | None):
    if states is None or isinstance(states, (State, str)):
        values = (states,)
    else:
        values = tuple(states)
    return tuple(state_value(state) for state in values)


class Router:
    """Registers the same handler in aiogram and maxapi routers."""

    def __init__(self, name: str | None = None) -> None:
        self.telegram = TelegramRouter(name=name)
        self.max = MaxRouter(router_id=name)

    def message(
        self,
        *,
        commands: Iterable[str] | None = None,
        states: Iterable[State | str | None] | State | str | None = None,
        with_state: bool = False,
        platforms: Iterable[Platform] | None = None,
    ) -> Callable[[Handler], Handler]:
        enabled = _platforms(platforms)
        command_values = tuple(commands or ())

        def decorator(handler: Handler) -> Handler:
            if Platform.TELEGRAM in enabled:
                self._register_telegram_message(
                    handler, command_values, states, with_state
                )
            if Platform.MAX in enabled:
                self._register_max_message(handler, command_values, states, with_state)
            return handler

        return decorator

    def callback(
        self,
        *,
        startswith: str | None = None,
        not_startswith: str | None = None,
        states: Iterable[State | str | None] | State | str | None = None,
        with_state: bool = False,
        platforms: Iterable[Platform] | None = None,
    ) -> Callable[[Handler], Handler]:
        if startswith is not None and not_startswith is not None:
            raise ValueError("Use startswith or not_startswith, not both")
        enabled = _platforms(platforms)

        def decorator(handler: Handler) -> Handler:
            if Platform.TELEGRAM in enabled:
                self._register_telegram_callback(
                    handler, startswith, not_startswith, states, with_state
                )
            if Platform.MAX in enabled:
                self._register_max_callback(
                    handler, startswith, not_startswith, states, with_state
                )
            return handler

        return decorator

    def _register_telegram_message(
        self,
        handler: Handler,
        commands: tuple[str, ...],
        states: Iterable[State | str | None] | State | str | None,
        with_state: bool,
    ) -> None:
        filters: list[Any] = []
        if commands:
            filters.append(TelegramCommand(*commands))
        if states is not None:
            filters.append(TelegramStateFilter(*_state_values(states)))

        if with_state:

            async def wrapped(
                message: TelegramNativeMessage,
                state: TelegramFSMContext,
            ) -> Any:
                return await handler(TelegramMessage(message), UnifiedContext(state))

        else:

            async def wrapped(message: TelegramNativeMessage) -> Any:
                return await handler(TelegramMessage(message))

        self.telegram.message.register(wrapped, *filters)

    def _register_max_message(
        self,
        handler: Handler,
        commands: tuple[str, ...],
        states: Iterable[State | str | None] | State | str | None,
        with_state: bool,
    ) -> None:
        filters: list[Any] = []
        if commands:
            filters.append(MaxCommand(list(commands)))
        if states is not None:
            filters.append(MaxStateFilter(*_state_values(states)))

        if with_state:

            async def wrapped(
                message: MessageCreated,
                context: MaxMemoryContext,
            ) -> Any:
                return await handler(MaxMessage(message), UnifiedContext(context))

        else:

            async def wrapped(message: MessageCreated) -> Any:
                return await handler(MaxMessage(message))

        self.max.message_created(*filters)(wrapped)

    def _register_telegram_callback(
        self,
        handler: Handler,
        startswith: str | None,
        not_startswith: str | None,
        states: Iterable[State | str | None] | State | str | None,
        with_state: bool,
    ) -> None:
        filters: list[Any] = []
        if startswith is not None:
            filters.append(TelegramF.data.startswith(startswith))
        elif not_startswith is not None:
            filters.append(~TelegramF.data.startswith(not_startswith))
        if states is not None:
            filters.append(TelegramStateFilter(*_state_values(states)))

        if with_state:

            async def wrapped(
                callback: TelegramCallbackQuery,
                state: TelegramFSMContext,
            ) -> Any:
                return await handler(TelegramCallback(callback), UnifiedContext(state))

        else:

            async def wrapped(callback: TelegramCallbackQuery) -> Any:
                return await handler(TelegramCallback(callback))

        self.telegram.callback_query.register(wrapped, *filters)

    def _register_max_callback(
        self,
        handler: Handler,
        startswith: str | None,
        not_startswith: str | None,
        states: Iterable[State | str | None] | State | str | None,
        with_state: bool,
    ) -> None:
        filters: list[Any] = []
        if startswith is not None:
            filters.append(MaxF.callback.payload.startswith(startswith))
        elif not_startswith is not None:
            filters.append(~MaxF.callback.payload.startswith(not_startswith))
        if states is not None:
            filters.append(MaxStateFilter(*_state_values(states)))

        if with_state:

            async def wrapped(
                callback: MessageCallback,
                context: MaxMemoryContext,
            ) -> Any:
                return await handler(MaxCallback(callback), UnifiedContext(context))

        else:

            async def wrapped(callback: MessageCallback) -> Any:
                return await handler(MaxCallback(callback))

        self.max.message_callback(*filters)(wrapped)
