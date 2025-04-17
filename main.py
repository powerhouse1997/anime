import os
import html
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.exceptions import TelegramRetryAfter

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

# Keywords to allow only anime-related news
ALLOWED_KEYWORDS = ["anime", "manga", "OVA", "episode", "film", "season", "crunchyroll", "funimation", "trailer"]

def is_anime_related(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ALLOWED_KEYWORDS)

# Fetch and parse ANN RSS feed
async def get_ann_news():
    async with aiohttp.ClientSession() as session:
        async with session.get(ANN_NEWS_URL) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
            root = ET.fromstring(text)
            items = root.findall(".//item")
            news = []
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                pub_date = item.find("pubDate").text
                description = item.find("description").text

                # Filter only anime-related
                if not is_anime_related(title):
                    continue

                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M UTC")
                except:
                    formatted_date = pub_date

                img_link = None
                if description and "<img" in description:
                    start = description.find("<img")
                    src_start = description.find("src=\"", start)
                    if src_start != -1:
                        src_start += len("src=\"")
                        src_end = description.find("\"", src_start)
                        if src_end != -1:
                            img_link = description[src_start:src_end]

                news.append({
                    "title": title,
                    "link": link,
                    "date": formatted_date,
                    "image": img_link
                })
            return news

# Format news item using Markdown

def format_news_item(item):
    title = html.escape(item["title"])
    link = html.escape(item["link"])
    date = html.escape(item["date"])
    return (
        f"\U0001F338 *{title}* \U0001F338\n\n"
        f"\U0001F4C5 *Published on:* `{date}`\n\n"
        f"\U0001F9E1 *Latest Update:*\n\n"
        f"\U0001F517 [Click to read full story]({link})\n\n"
        f"\u2601\ufe0f _Take a gentle pause and enjoy the latest anime happenings._\n\n"
        f"\U0001F4AC Share your feelings with the community!\n\n"
        f"#AnimeNews"
    )

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("\U0001F44B Welcome! Use /news to get the latest anime news from Anime News Network.")

@dp.message(F.text == "/news")
async def cmd_news(message: Message):
    await message.answer("\U0001F4F0 Fetching the latest anime news...")
    news_list = await get_ann_news()
    if not news_list:
        await message.answer("\u274C Couldn't fetch news right now.")
        return
    for item in news_list[:5]:
        for chat_id in CHANNEL_IDS:
            await try_send_news(chat_id=chat_id.strip(), item=item)
            await asyncio.sleep(1.5)

# Retry-safe message/photo sender with optional pinning
async def try_send_news(chat_id, item):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if item.get("image"):
                msg = await bot.send_photo(chat_id=chat_id, photo=item["image"], caption=format_news_item(item))
            else:
                msg = await bot.send_message(chat_id=chat_id, text=format_news_item(item), disable_web_page_preview=False)

            if chat_id == PINNABLE_ID and attempt == 0:
                try:
                    await bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=True)
                except Exception as pin_error:
                    print(f"Pinning failed: {pin_error}")
            return

        except TelegramRetryAfter as e:
            print(f"Rate limit hit. Waiting {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            print(f"Error sending message: {e}")
            await asyncio.sleep(2)

# Automatically check and send new news
async def check_and_send_news():
    news_list = await get_ann_news()
    for item in news_list:
        if item["link"] not in sent_cache:
            for chat_id in CHANNEL_IDS:
                await try_send_news(chat_id=chat_id.strip(), item=item)
            sent_cache.append(item["link"])
            save_cache()
            await asyncio.sleep(2)

# Main entry point
async def main():
    scheduler.add_job(check_and_send_news, "interval", minutes=10)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
