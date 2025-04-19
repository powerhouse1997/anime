import aiohttp
import asyncio
import html
from datetime import datetime, timedelta
from main import bot, CHANNEL_IDS

# Dummy fetch function – replace this with your actual API logic
async def fetch_upcoming_releases(early=False):
    """
    Fetch upcoming anime releases from your API or data source.
    Returns a list of dictionaries: { title, date, image (optional) }
    """
    # Example static mockup (replace this with actual API fetching logic)
    example = [
        {
            "title": "One Piece",
            "date": (datetime.utcnow() + timedelta(days=1 if early else 0)).strftime("%Y-%m-%d"),
            "image": "https://cdn.myanimelist.net/images/anime/6/73245.jpg"
        },
        {
            "title": "Jujutsu Kaisen Season 2",
            "date": (datetime.utcnow() + timedelta(days=1 if early else 0)).strftime("%Y-%m-%d"),
            "image": "https://cdn.myanimelist.net/images/anime/1171/109222.jpg"
        }
    ]
    return example

# Main notification function
async def notify_releases(early=False, manual_chat_id=None):
    releases = await fetch_upcoming_releases(early=early)

    if not releases:
        message = "😔 No upcoming releases found."
        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            await bot.send_message(chat_id=chat_id.strip(), text=message)
        return

    for release in releases:
        title = html.escape(release.get("title", "Unknown"))
        date = html.escape(release.get("date", "Unknown"))
        image = release.get("image")

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"📅 <b>Release Date:</b> <code>{date}</code>\n\n"
            f"#UpcomingAnime"
        )

        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            try:
                if image:
                    await bot.send_photo(
                        chat_id=chat_id.strip(),
                        photo=image,
                        caption=caption,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id.strip(),
                        text=caption,
                        parse_mode="HTML"
                    )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error sending release to {chat_id}]: {e}")
