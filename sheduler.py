import asyncio
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
from datetime import datetime
from aiogram import Bot

# Fetch upcoming releases (you can replace this with actual API fetching)
async def fetch_released_anime():
    # Replace with your API call to fetch the released anime data
    # Example static mockup (replace with real API fetching logic)
    example = [
        {
            "title": "One Piece",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "image": "https://cdn.myanimelist.net/images/anime/6/73245.jpg",
            "url": "https://www.example.com/one-piece"  # Replace with actual anime link
        },
        {
            "title": "Jujutsu Kaisen",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "image": "https://cdn.myanimelist.net/images/anime/1171/109222.jpg",
            "url": "https://www.example.com/jujutsu-kaisen"  # Replace with actual anime link
        }
    ]
    return example

# Function to create the "Watch Now" button
def create_watch_button(url):
    button = InlineKeyboardButton(text="Watch Now", url=url)
    keyboard = InlineKeyboardMarkup().add(button)
    return keyboard

# Function to send notifications for released anime
async def notify_releases(bot: Bot, CHANNEL_IDS, early=False, manual_chat_id=None):
    releases = await fetch_released_anime()  # Get anime data

    if not releases:
        message = "😔 No upcoming releases found."
        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
        return

    for release in releases:
        title = release.get("title", "Unknown")
        date = release.get("date", "Unknown")
        image = release.get("image", None)
        url = release.get("url", "")  # The URL for "Watch Now" button

        caption = f"🎬 *{title}*\n📅 Released: {date}\n"

        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            try:
                keyboard = create_watch_button(url)  # Add "Watch Now" button
                if image:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=image,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=caption,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error sending release to {chat_id}]: {e}")
