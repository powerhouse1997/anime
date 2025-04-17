import os
import html
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InputMediaPhoto
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
ANN_NEWS_URL = "https://www.animenewsnetwork.com/all/rss.xml"
NEWS_CACHE_FILE = "sent_ann_news.json"

# Initialize bot with default HTML parse mode
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
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

                # Try to extract an image URL from description (if present)
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
                    "date": pub_date,
                    "image": img_link
                })
            return news

# Slice of Life - Soft Vibes style

def format_news_item(item):
    title = html.escape(item["title"])
    link = html.escape(item["link"])
    date = html.escape(item["date"])
    return (
        f"🌸 <b><u>{title}</u></b> 🌸\n\n"
        f"📅 <b>Published on:</b> <code>{date}</code>\n\n"
        f"🧡 <b>Latest Update:</b>\n\n"
        f"🔗 <a href='{link}'>Click to read full story</a>\n\n"
        f"☁️ <i>Take a gentle pause and enjoy the latest anime happenings.</i>\n\n"
        f"💬 Share your feelings with the community!\n\n"
        f"#SliceOfLife #AnimeNews"
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
        if item.get("image"):
            await message.answer_photo(photo=item["image"], caption=format_news_item(item))
        else:
            await message.answer(format_news_item(item), disable_web_page_preview=False)

# Automatically check and send new news
async def check_and_send_news():
    news_list = await get_ann_news()
    for item in news_list:
        if item["link"] not in sent_cache:
            try:
                if item.get("image"):
                    await bot.send_photo(chat_id=os.getenv("NEWS_CHAT_ID", "your-chat-id"), photo=item["image"], caption=format_news_item(item))
                else:
                    await bot.send_message(chat_id=os.getenv("NEWS_CHAT_ID", "your-chat-id"), text=format_news_item(item), disable_web_page_preview=False)
                sent_cache.append(item["link"])
                save_cache()
            except Exception as e:
                print(f"Failed to send news: {e}")

# Main entry point
async def main():
    scheduler.add_job(check_and_send_news, "interval", minutes=10)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
