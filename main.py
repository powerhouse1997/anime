
import asyncio
from aiogram import Bot

async def run():
    bot = Bot(token="YOUR_BOT_TOKEN")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted.")
    await bot.session.close()

asyncio.run(run())