import pytest

from telegram_with_max import Platform, Router, State, StatesGroup


class Form(StatesGroup):
    value = State()


def test_handlers_are_registered_for_both_platforms():
    router = Router(name="both")

    @router.message(commands=["start"], states=[Form.value], with_state=True)
    async def message_handler(message, state):
        return None

    @router.callback(startswith="demo:")
    async def callback_handler(callback):
        return None

    assert len(router.telegram.message.handlers) == 1
    assert len(router.telegram.callback_query.handlers) == 1
    assert len(router.max.event_handlers) == 2


def test_handler_can_be_limited_to_one_platform():
    router = Router()

    @router.message(platforms=[Platform.TELEGRAM])
    async def telegram_only(message):
        return None

    assert len(router.telegram.message.handlers) == 1
    assert router.max.event_handlers == []


def test_callback_prefix_filters_are_mutually_exclusive():
    router = Router()
    with pytest.raises(ValueError, match="startswith"):
        router.callback(startswith="yes", not_startswith="no")
