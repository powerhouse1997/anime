import feedparser
import json
import os
from aiogram import Bot
from utils.html import escape_html

NEWS_FEED_URLS = ["https://www.animenewsnetwork.com/all/rss.xml"]
CACHE_FILE = "sent_news_cache.json"

def load_sent_cache():
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r") as f:
        return set(json.load(f))

def save_sent_cache(sent):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(sent), f)

async def post_latest_news(bot: Bot):
    sent = load_sent_cache()
    chat_id = "521798593"  # Replace with actual chat ID or channel
    for url in NEWS_FEED_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = entry.link
            if link in sent or not any(kw in entry.title.lower() for kw in ["anime", "manga"]):
                continue
            msg = f"<b>{escape_html(entry.title)}</b>\\n\\n{escape_html(entry.summary)}\\n<a href='{link}'>Read more</a>"
            await bot.send_message(chat_id, msg)
            sent.add(link)
    save_sent_cache(sent)

async def fetch_latest_news(limit=5):
    items = []
    for url in NEWS_FEED_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if not any(kw in entry.title.lower() for kw in ["anime", "manga"]):
                continue
            items.append({"title": entry.title, "summary": entry.summary, "link": entry.link})
            if len(items) >= limit:
                return items
    return items
