import os
import json
import aiohttp
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.exceptions import TelegramRetryAfter
from main import bot, CHAT_IDS  # Adjust import to use CHAT_IDS

SHIKIMORI_API_URL = "https://shikimori.one/api/calendar"
RELEASE_CACHE_FILE = "sent_releases_cache.json"

# Load release cache or initialize it
if os.path.exists(RELEASE_CACHE_FILE):
    with open(RELEASE_CACHE_FILE, "r") as f:
        release_cache = json.load(f)
else:
    release_cache = []

def save_release_cache():
    with open(RELEASE_CACHE_FILE, "w") as f:
        json.dump(release_cache, f)

async def fetch_shikimori_releases():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SHIKIMORI_API_URL) as response:
                if response.status != 200:
                    return []
                return await response.json()
    except Exception as e:
        print(f"Error fetching Shikimori releases: {e}")
        return []

def should_notify(release_date_str, delta_days=0):
    try:
        date_obj = datetime.strptime(release_date_str, "%Y-%m-%d")
        target_date = datetime.utcnow().date() + timedelta(days=delta_days)
        return date_obj == target_date
    except Exception:
        return False

def format_release_message(item, early=False):
    date = item.get("date", "Unknown Date")
    anime = item.get("anime", {})
    name = anime.get("russian") or anime.get("name") or "Unknown Title"
    episode = item.get("episode", "N/A")
    kind = anime.get("kind", "anime").capitalize()
    url = f"https://shikimori.one{anime.get('url', '')}"

    prefix = "🗓️ Coming Tomorrow:" if early else "🚨 New Release Today!"
    return (
        f"{prefix}\n\n"
        f"*{name}*\n"
        f"📺 Type: {kind}\n"
        f"🎬 Episode: {episode}\n"
        f"📅 Date: `{date}`\n"
        f"🔗 [View on Shikimori]({url})"
    )

async def notify_releases(early=False):
    releases = await fetch_shikimori_releases()
    for item in releases:
        date = item.get("date")
        if not should_notify(date, delta_days=1 if early else 0):
            continue

        cache_key = f"{item['id']}_{'early' if early else 'day'}"
        if cache_key in release_cache:
            continue

        message = format_release_message(item, early=early)
        for chat_id in CHAT_IDS:  # Using CHAT_IDS instead of CHANNEL_IDS
            for attempt in range(3):
                try:
                    await bot.send_message(chat_id.strip(), message, disable_web_page_preview=True)
                    break
                except TelegramRetryAfter as e:
                    print(f"Rate limit. Sleeping {e.retry_after}s...")
                    await asyncio.sleep(e.retry_after)
                except Exception as e:
                    print(f"Failed to send release msg: {e}")
                    await asyncio.sleep(2)

        release_cache.append(cache_key)
        save_release_cache()
        await asyncio.sleep(2)

def setup_scheduled_jobs(scheduler: AsyncIOScheduler):
    # Schedule notifications for tomorrow's releases (early reminder) and today's releases
    scheduler.add_job(lambda: asyncio.create_task(notify_releases(early=True)), "cron", hour=8)
    scheduler.add_job(lambda: asyncio.create_task(notify_releases(early=False)), "cron", hour=10)
