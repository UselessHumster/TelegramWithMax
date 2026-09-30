# TelegramWithMax

Небольшая Python-библиотека, позволяющая писать общие обработчики для ботов
Telegram и MAX. Один процесс запускает polling обеих платформ, а обработчики
получают единые объекты сообщений, callback-событий и FSM-контекста.

Проект находится на ранней стадии. Версия `0.2.1` поддерживает текстовые
сообщения, команды, callback-кнопки и состояния. Медиа, webhook и опросы пока
не входят в публичный API.

## Установка

```bash
pip install git+ssh://git@github.com/UselessHumster/TelegramWithMax.git
```

Для разработки:

```bash
git clone git@github.com:UselessHumster/TelegramWithMax.git
cd TelegramWithMax
uv sync
```

## Быстрый старт

```python
import asyncio
import os

from telegram_with_max import App, InlineButton, InlineKeyboard, Router

router = Router()


@router.message(commands=["start"])
async def start(message):
    keyboard = InlineKeyboard(
        [[InlineButton(text="Нажми меня", callback_data="hello")]]
    )
    await message.answer("Привет из общего обработчика!", reply_markup=keyboard)


@router.callback(startswith="hello")
async def hello(callback):
    await callback.answer("Готово")


async def main():
    app = App(
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        max_token=os.environ["MAX_BOT_TOKEN"],
    )
    app.include_router(router)
    await app.run_polling()


asyncio.run(main())
```

Для единого старта через Telegram `/start`, MAX `/start` и событие запуска MAX
используйте `@router.started()`. Произвольное исходящее сообщение отправляется
без обращения к нативным клиентам:

```python
await app.send_message(
    platform=Platform.MAX,
    chat_id=chat_id,
    text="Готово",
)
```

У входящего сообщения доступны общие поля `display_name` и `username`.

Полный запускаемый пример находится в [`examples/echo_bot.py`](examples/echo_bot.py).

Для Telegram-прокси передайте `telegram_proxy="http://127.0.0.1:18080"`
в `App`. MAX продолжает использовать прямое подключение.

## Состояния

```python
from telegram_with_max import State, StatesGroup


class Form(StatesGroup):
    name = State()


@router.message(commands=["form"], with_state=True)
async def begin(message, state):
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?")


@router.message(states=[Form.name], with_state=True)
async def save_name(message, state):
    await state.update_data(name=message.text)
    await state.clear()
```

Состояния и идентификаторы пользователей хранятся отдельно для каждой
платформы. Связывание Telegram- и MAX-аккаунтов остаётся задачей приложения.
