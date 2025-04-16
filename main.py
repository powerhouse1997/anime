import os
import html
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
ANN_NEWS_URL = "https://www.animenewsnetwork.com/all/rss.xml"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Parse ANN's RSS feed and return a list of news items
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
                news.append({
                    "title": title,
                    "link": link,
                    "date": pub_date
                })
            return news

def format_news_item(item):
    title = html.escape(item["title"])
    link = html.escape(item["link"])
    date = html.escape(item["date"])
    return f"<b>{title}</b>\n🗓️ {date}\n<a href='{link}'>Read more</a>"

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("👋 Welcome! Use /news to get the latest anime news from Anime News Network.")

@dp.message_handler(commands=["news"])
async def news(message: types.Message):
    await message.answer("📰 Fetching anime news...")
    news_list = await get_ann_news()
    if not news_list:
        await message.answer("❌ Couldn't fetch news right now.")
        return

    for item in news_list[:5]:  # top 5
        await message.answer(format_news_item(item), disable_web_page_preview=False)

if __name__ == "__main__":
    executor.start_polling(dp)
