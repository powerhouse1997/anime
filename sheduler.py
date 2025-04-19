import aiohttp
import asyncio
import html
from datetime import datetime, timedelta

# Update function to accept bot and channel IDs as arguments
async def notify_releases(bot, CHANNEL_IDS, early=False, manual_chat_id=None):
    """
    Function to fetch upcoming releases and send notifications.
    """
    upcoming_releases = await fetch_upcoming_releases(early=early)
    today_releases = await fetch_today_releases()

    # If no upcoming releases or today's releases, send a "No releases" message
    if not upcoming_releases and not today_releases:
        message = "😔 No upcoming releases or releases today."
        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            await bot.send_message(chat_id=str(chat_id).strip(), text=message)  # Ensure chat_id is a string
        return

    # Send today's releases
    if today_releases:
        for release in today_releases:
            await send_release_message(bot, release, CHANNEL_IDS, manual_chat_id)

    # Send upcoming releases
    if upcoming_releases:
        for release in upcoming_releases:
            await send_release_message(bot, release, CHANNEL_IDS, manual_chat_id)


async def send_release_message(bot, release, CHANNEL_IDS, manual_chat_id):
    """
    Helper function to send a formatted release message.
    """
    title = html.escape(release.get("title", "Unknown"))
    date = html.escape(release.get("date", "Unknown"))
    genres = ", ".join(release.get("genres", []))  # Join genres as a comma-separated string
    rating = release.get("rating", "Unknown")
    episodes = release.get("episodes", "Unknown")
    image = release.get("image")

    caption = (
        f"🎬 <b>{title}</b>\n"
        f"📅 <b>Release Date:</b> <code>{date}</code>\n\n"
        f"🌟 <b>Rating:</b> <code>{rating}</code>\n"
        f"📈 <b>Genres:</b> <code>{genres}</code>\n"
        f"📺 <b>Episodes:</b> <code>{episodes}</code>\n\n"
        f"#AnimeRelease"
    )

    targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
    for chat_id in targets:
        try:
            if image:
                # Send the image with the caption
                await bot.send_photo(
                    chat_id=str(chat_id).strip(),  # Ensure chat_id is a string
                    photo=image,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                # Send the caption if no image is available
                await bot.send_message(
                    chat_id=str(chat_id).strip(),  # Ensure chat_id is a string
                    text=caption,
                    parse_mode="HTML"
                )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[Error sending release to {chat_id}]: {e}")


async def fetch_upcoming_releases(early=False):
    """
    Fetch upcoming anime releases from Shikimori Calendar API.
    Returns a list of dictionaries: { title, date, genres, rating, episodes, image (optional) }
    """
    url = "https://shikimori.one/api/calendar"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    params = {"date": today, "limit": 5, "order": "airing_at"}  # Get anime airing today with limit

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error fetching from Shikimori Calendar API: {resp.status}")
                    return []
                data = await resp.json()

                # Extract necessary data
                upcoming_anime = []
                for anime in data:
                    title = anime.get("name", "Unknown")
                    release_date = anime.get("aired_on", None)
                    genres = [genre["name"] for genre in anime.get("genres", [])]
                    rating = anime.get("score", "No rating available")
                    episodes = anime.get("episodes", "Unknown")
                    image = anime.get("image", {}).get("original", None)

                    if release_date:
                        release_date = datetime.strptime(release_date, "%Y-%m-%d")
                        release_date = release_date.strftime("%Y-%m-%d")
                    else:
                        release_date = "Unknown"

                    upcoming_anime.append({
                        "title": title,
                        "date": release_date,
                        "genres": genres,
                        "rating": rating,
                        "episodes": episodes,
                        "image": image
                    })
                return upcoming_anime
        
        except Exception as e:
            print(f"Error while fetching upcoming releases: {e}")
            return []


async def fetch_today_releases():
    """
    Fetch today's anime releases from Shikimori Calendar API.
    Returns a list of dictionaries: { title, date, genres, rating, episodes, image (optional) }
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    url = "https://shikimori.one/api/calendar"
    params = {"date": today, "limit": 10}  # Fetch anime that are released today (status=2)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"Error fetching from Shikimori Calendar API: {resp.status}")
                    return []
                data = await resp.json()

                # Filter releases for today
                today_releases = []
                for anime in data:
                    release_date = anime.get("aired_on", None)
                    if release_date and release_date == today:
                        title = anime.get("name", "Unknown")
                        genres = [genre["name"] for genre in anime.get("genres", [])]
                        rating = anime.get("score", "No rating available")
                        episodes = anime.get("episodes", "Unknown")
                        image = anime.get("image", {}).get("original", None)
                        
                        today_releases.append({
                            "title": title,
                            "date": release_date,
                            "genres": genres,
                            "rating": rating,
                            "episodes": episodes,
                            "image": image
                        })
                return today_releases
        
        except Exception as e:
            print(f"Error while fetching today's releases: {e}")
            return []
