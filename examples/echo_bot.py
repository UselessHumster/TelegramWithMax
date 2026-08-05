import asyncio
import os

from telegram_with_max import App, InlineButton, InlineKeyboard, Router

router = Router(name="echo")


@router.message(commands=["start"])
async def start(message):
    keyboard = InlineKeyboard(
        [[InlineButton(text="Проверить callback", callback_data="demo:hello")]]
    )
    await message.answer(
        f"Привет! Вы написали из {message.platform.value}.",
        reply_markup=keyboard,
    )


@router.callback(startswith="demo:")
async def callback_pressed(callback):
    await callback.answer("Callback работает")


@router.message()
async def echo(message):
    if message.text:
        await message.answer(message.text)


async def main():
    app = App(
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        max_token=os.environ["MAX_BOT_TOKEN"],
    )
    app.include_router(router)
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
