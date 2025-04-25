import aiohttp
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.enums import ParseMode

# Anilist API URL and Query to get currently airing anime
ANILIST_API_URL = "https://graphql.anilist.co"

QUERY = """
query ($page: Int, $perPage: Int) {
    Page(page: $page, perPage: $perPage) {
        media(type: ANIME, status: AIRING) {
            id
            title {
                romaji
                english
            }
            startDate {
                year
                month
                day
            }
            coverImage {
                large
            }
            siteUrl
        }
    }
}
"""

async def fetch_released_anime():
    """
    Fetch the released anime from Anilist API.
    Returns a list of dictionaries with title, release date, image, and URL.
    """
    async with aiohttp.ClientSession() as session:
        variables = {"page": 1, "perPage": 5}  # Adjust the page and perPage as needed
        async with session.post(ANILIST_API_URL, json={"query": QUERY, "variables": variables}) as response:
            if response.status == 200:
                data = await response.json()
                releases = []

                for media in data['data']['Page']['media']:
                    title = media['title']['romaji'] if media['title']['romaji'] else media['title']['english']
                    date = f"{media['startDate']['year']}-{media['startDate']['month']}-{media['startDate']['day']}"
                    image = media['coverImage']['large']
                    url = media['siteUrl']

                    releases.append({
                        "title": title,
                        "date": date,
                        "image": image,
                        "url": url
                    })

                return releases
            else:
                print(f"Error fetching from Anilist API: {response.status}")
                return []

async def send_release_message(bot: Bot, channel_ids, release):
    """
    Send a formatted message with anime release details to the specified channels.
    """
    title = release.get("title")
    date = release.get("date")
    image = release.get("image")
    url = release.get("url")

    caption = (
        f"🎬 <b>{title}</b>\n"
        f"📅 <b>Release Date:</b> <code>{date}</code>\n"
        f"🔗 <a href='{url}'>Watch Now</a>\n\n"
        f"#ReleasedAnime"
    )

    for chat_id in channel_ids:
        try:
            if image:
                await bot.send_photo(
                    chat_id=str(chat_id).strip(),
                    photo=image,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=str(chat_id).strip(),
                    text=caption,
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            print(f"[Error sending release to {chat_id}]: {e}")

async def notify_releases(bot: Bot, channel_ids):
    """
    Fetches and sends release messages.
    """
    try:
        releases = await fetch_released_anime()
        if releases:
            for release in releases:
                await send_release_message(bot, channel_ids, release)
    except Exception as e:
        print(f"Error during scheduled notification: {e}")
