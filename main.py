from aiogram import F
from aiogram.enums import ParseMode
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from handlers import anime, news, schedule
from scheduler import setup_scheduler

async def on_startup(bot: Bot, dispatcher: Dispatcher):
    setup_scheduler(bot, dispatcher)

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML, session=AiohttpSession())
    dp = Dispatcher()

    anime.register(dp)
    news.register(dp)
    schedule.register(dp)

    await on_startup(bot, dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
