
import asyncio
from aiogram import Bot

async def run():
    bot = Bot(token="7853195961:AAEjeCiDPbZIahkZ77tGFYLmo6oGlOyV_uo")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted.")
    await bot.session.close()

asyncio.run(run())