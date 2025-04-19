import os
import html
import aiohttp
import asyncio
from datetime import datetime
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Load bot token and chat/channel IDs
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
CHANNEL_IDS = os.getenv("CHAT_IDS", "your-chat-id").split(",")

# Setup bot
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

# Simulated dummy release data
async def fetch_upcoming_releases(early=False):
    # You can replace this with actual API integration (e.g., Shikimori or Anilist)
    return [
        {"title": "My Hero Academia S7", "date": "2025-04-27"},
        {"title": "Chainsaw Man S2", "date": "2025-05-01"}
    ] if early else []

def format_release_message(releases):
    if not releases:
        return "😔 No upcoming releases found."
    
    lines = ["📅 *Upcoming Anime Releases:*"]
    for r in releases:
        title = html.escape(r["title"])
        date = html.escape(r["date"])
        lines.append(f"• *{title}* — `{date}`")
    return "\n".join(lines)

# Main release notification logic
async def notify_releases(early=False, manual_chat_id=None):
    releases = await fetch_upcoming_releases(early=early)
    message = format_release_message(releases)

    if manual_chat_id:
        # Sent manually via /upcoming
        await bot.send_message(chat_id=manual_chat_id, text=message)
    else:
        # Scheduled push to all channels
        for chat_id in CHANNEL_IDS:
            await bot.send_message(chat_id=chat_id.strip(), text=message)
            await asyncio.sleep(1)
