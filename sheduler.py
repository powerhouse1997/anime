import aiohttp
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

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

async def notify_releases(bot: Bot, channel_ids, early=False):
    """
    Function to fetch recently released anime and notify specified channels.
    """
    releases = await fetch_released_anime()

    if not releases:
        message = "😔 No recently released anime found."
        for chat_id in channel_ids:
            await bot.send_message(chat_id=str(chat_id).strip(), text=message)  # Ensure chat_id is a string
        return

    # Send release notifications
    for release in releases:
        await send_release_message(bot, channel_ids, release)

async def scheduled_notifications(bot: Bot, channel_ids):
    """
    Function to handle daily scheduled notifications for newly released anime.
    """
    while True:
        try:
            await notify_releases(bot, channel_ids)
        except Exception as e:
            print(f"Error during scheduled notification: {e}")
        # Sleep for 24 hours (86400 seconds)
        await asyncio.sleep(86400)
