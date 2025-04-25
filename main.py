import os
import html
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import sheduler  # Importing the sheduler after Bot initialization
import json  # Import json here as it's used in this file

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
CHANNEL_IDS = os.getenv("CHAT_IDS", "your-chat-id").split(",")
PINNABLE_ID = os.getenv("PIN_ID", CHANNEL_IDS[0])
ANN_NEWS_URL = "https://www.animenewsnetwork.com/all/rss.xml"
NEWS_CACHE_FILE = "sent_ann_news.json"

# Initialize bot with default Markdown parse mode
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

# Load or initialize cache
if os.path.exists(NEWS_CACHE_FILE):
    with open(NEWS_CACHE_FILE, "r") as f:
        sent_cache = json.load(f)
else:
    sent_cache = []

# Save updated cache
def save_cache():
    with open(NEWS_CACHE_FILE, "w") as f:
        json.dump(sent_cache, f)


@dp.message(F.text == "/upcoming")
async def cmd_upcoming(message: Message):
    """
    Command to fetch and notify about upcoming anime releases.
    """
    # Call the correct function name from sheduler.py
    await sheduler.scheduled_notifications(bot, CHANNEL_IDS)


async def main():
    # Call the correct function name in the scheduler as well
    scheduler.add_job(sheduler.scheduled_notifications, "interval", minutes=10, args=[bot, CHANNEL_IDS])
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
