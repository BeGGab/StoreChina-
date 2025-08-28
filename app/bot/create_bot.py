from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings


bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def start_bot():
    count = 0
    for admin in settings.ADMIN_ID:
        try:
            await bot.send_message(chat_id=admin, text=f"Я запущен🥳")
            count += 1
        except:
            pass


async def stop_bot():
    count = 0
    for admin in settings.ADMIN_ID:
        try:
            await bot.send_message(chat_id=admin, text=f"Я остановлен😔. За что?")
            count += 1
        except:
            pass