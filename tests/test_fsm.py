from unittest.mock import AsyncMock

import pytest

from telegram_with_max import State, StatesGroup, UnifiedContext


class Form(StatesGroup):
    name = State()
    age = State("form:age")


def test_states_get_stable_platform_independent_names():
    assert str(Form.name).endswith("Form:name")
    assert str(Form.age) == "form:age"
    assert Form.states() == (Form.name, Form.age)


@pytest.mark.asyncio
async def test_unified_context_delegates_using_string_state():
    raw = AsyncMock()
    raw.get_state.return_value = str(Form.name)
    raw.get_data.return_value = {"name": "Max"}
    raw.update_data.return_value = {"name": "Telegram"}
    context = UnifiedContext(raw)

    await context.set_state(Form.name)
    assert await context.get_state() == str(Form.name)
    assert await context.get_data() == {"name": "Max"}
    assert await context.update_data(name="Telegram") == {"name": "Telegram"}
    await context.set_data({"name": "Both"})
    await context.finish()

    raw.set_state.assert_awaited_once_with(str(Form.name))
    raw.set_data.assert_awaited_once_with({"name": "Both"})
    raw.clear.assert_awaited_once()
