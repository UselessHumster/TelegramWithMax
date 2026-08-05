from __future__ import annotations

from typing import Any


class State:
    """Platform-independent FSM state descriptor."""

    def __init__(self, value: str | None = None) -> None:
        self._value = value

    def __set_name__(self, owner: type, name: str) -> None:
        if self._value is None:
            self._value = f"{owner.__module__}.{owner.__qualname__}:{name}"

    @property
    def value(self) -> str:
        if self._value is None:
            raise RuntimeError("State is not bound to a StatesGroup")
        return self._value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"State({self.value!r})"


class StatesGroup:
    """Namespace for related :class:`State` descriptors."""

    @classmethod
    def states(cls) -> tuple[State, ...]:
        return tuple(value for value in vars(cls).values() if isinstance(value, State))


def state_value(state: State | str | None) -> str | None:
    if state is None:
        return None
    return str(state)


class UnifiedContext:
    """Common facade over aiogram and maxapi FSM contexts."""

    def __init__(self, context: Any) -> None:
        self.raw = context

    async def set_state(self, state: State | str | None) -> None:
        await self.raw.set_state(state_value(state))

    async def get_state(self) -> str | None:
        state = await self.raw.get_state()
        return None if state is None else str(state)

    async def clear(self) -> None:
        await self.raw.clear()

    async def finish(self) -> None:
        await self.clear()

    async def get_data(self) -> dict[str, Any]:
        return await self.raw.get_data()

    async def set_data(self, data: dict[str, Any]) -> None:
        await self.raw.set_data(data)

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        return await self.raw.update_data(**kwargs)
