import os
import html
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.exceptions import TelegramRetryAfter
from aiogram import types
from aiogram.types import ParseMode
from sheduler import notify_releases  # Import notify_releases from your scheduler
from bot_config import bot, CHAT_IDS, PINNABLE_ID
from sheduler import setup_scheduled_jobs  # Import scheduler setup

ANN_NEWS_URL = "https://www.animenewsnetwork.com/all/rss.xml"
NEWS_CACHE_FILE = "sent_ann_news.json"

dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

if os.path.exists(NEWS_CACHE_FILE):
    with open(NEWS_CACHE_FILE, "r") as f:
        sent_cache = json.load(f)
else:
    sent_cache = []

def save_cache():
    with open(NEWS_CACHE_FILE, "w") as f:
        json.dump(sent_cache, f)

ALLOWED_KEYWORDS = ["anime", "manga", "OVA", "episode", "film", "season", "crunchyroll", "funimation", "trailer"]

def is_anime_related(title):
    return any(keyword in title.lower() for keyword in ALLOWED_KEYWORDS)

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
    await message.answer("👋 Welcome! Use /news to get the latest anime news from Anime News Network.")

@dp.message(F.text == "/news")
async def cmd_news(message: Message):
    await message.answer("📰 Fetching the latest anime news...")
    news_list = await get_ann_news()
    if not news_list:
        await message.answer("❌ Couldn't fetch news right now.")
        return
    for item in news_list[:5]:
        for chat_id in CHAT_IDS:
            await try_send_news(chat_id=chat_id.strip(), item=item)
            await asyncio.sleep(1.5)
# Add the /upcoming command handler
@dp.message(F.text == "/upcoming")
async def cmd_upcoming(message: Message):
    # This command will send upcoming releases right away
    await message.answer("🕑 Fetching upcoming releases...")
    
    try:
        # Trigger upcoming releases from Shikimori API (early notifications)
        await notify_releases(early=True)
        await message.answer("🚨 Upcoming releases sent!")
    except Exception as e:
        await message.answer(f"❌ Error occurred: {str(e)}")

async def try_send_news(chat_id, item):
    for attempt in range(3):
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

async def check_and_send_news():
    news_list = await get_ann_news()
    for item in news_list:
        if item["link"] not in sent_cache:
            for chat_id in CHAT_IDS:
                await try_send_news(chat_id=chat_id.strip(), item=item)
            sent_cache.append(item["link"])
            save_cache()
            await asyncio.sleep(2)

async def main():
    scheduler.add_job(check_and_send_news, "interval", minutes=10)
    setup_scheduled_jobs(scheduler)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
