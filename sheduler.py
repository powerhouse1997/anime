import aiohttp
import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

ANI_LIST_API_URL = "https://graphql.anilist.co"

# Function to fetch released anime from AniList
async def fetch_released_anime():
    query = '''
    query {
        Page(page: 1, perPage: 10) {
            media(type: ANIME, status: FINISHED) {
                title {
                    romaji
                    english
                    native
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
    '''

    async with aiohttp.ClientSession() as session:
        async with session.post(ANI_LIST_API_URL, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()
                released_anime = []
                for media in data["data"]["Page"]["media"]:
                    title = media["title"]["romaji"] or media["title"]["english"] or media["title"]["native"]
                    release_date = datetime(media["startDate"]["year"], media["startDate"]["month"], media["startDate"]["day"]).strftime('%Y-%m-%d')
                    image = media["coverImage"]["large"]
                    url = media["siteUrl"]
                    released_anime.append({
                        'title': title,
                        'release_date': release_date,
                        'image': image,
                        'url': url
                    })
                return released_anime
            else:
                print("Error fetching from AniList API:", response.status)
                return []

# Function to create inline button for watching
def create_watch_button(url):
    button = InlineKeyboardButton(text="Watch Now", url=url)
    keyboard = InlineKeyboardMarkup().add(button)
    return keyboard

# Function to send released anime to your channels
async def send_released_anime(bot, CHANNEL_IDS):
    released_anime = await fetch_released_anime()

    if not released_anime:
        message = "😔 No recently released anime found."
        for chat_id in CHANNEL_IDS:
            await bot.send_message(chat_id, message)
        return

    for anime in released_anime:
        title = anime['title']
        release_date = anime['release_date']
        image = anime['image']
        url = anime['url']
        
        caption = (
            f"🎬 *{title}*\n"
            f"📅 Released: {release_date}\n"
            f"#ReleasedAnime"
        )

        keyboard = create_watch_button(url)

        for chat_id in CHANNEL_IDS:
            try:
                if image:
                    await bot.send_photo(chat_id=chat_id, photo=image, caption=caption, reply_markup=keyboard, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard, parse_mode="Markdown")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error sending release to {chat_id}]: {e}")
