import aiohttp
import asyncio
import html
from datetime import datetime, timezone, timedelta

ANILIST_API = "https://graphql.anilist.co"

# Fetch upcoming anime releases from Anilist API
async def fetch_anilist_upcoming():
    query = """
    query ($now: Int) {
      Page(perPage: 10) {
        airingSchedules(sort: TIME, airingAt_greater: $now) {
          airingAt
          episode
          media {
            title {
              romaji
            }
            coverImage {
              large
            }
            siteUrl
          }
        }
      }
    }
    """

    now_timestamp = int(datetime.now(tz=timezone.utc).timestamp())
    variables = {"now": now_timestamp}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(ANILIST_API, json={"query": query, "variables": variables}) as resp:
                if resp.status != 200:
                    print(f"Anilist API error: {resp.status}")
                    return []

                data = await resp.json()
                return data["data"]["Page"]["airingSchedules"]
    except Exception as e:
        print(f"Error fetching from Anilist API: {e}")
        return []

# Function to send upcoming releases as messages
async def notify_releases(bot, CHANNEL_IDS, early=False, manual_chat_id=None):
    releases = await fetch_anilist_upcoming()

    if not releases:
        message = "😔 No upcoming releases found."
        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            await bot.send_message(chat_id=str(chat_id).strip(), text=message)  # Ensure chat_id is a string
        return

    for release in releases:
        title = html.escape(release["media"]["title"]["romaji"])
        date = datetime.utcfromtimestamp(release["airingAt"]).strftime("%Y-%m-%d %H:%M:%S UTC")
        image = release["media"]["coverImage"]["large"]
        url = release["media"]["siteUrl"]
        episode = release["episode"]

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"📅 <b>Release Date:</b> <code>{date}</code>\n"
            f"📝 <b>Episode:</b> {episode}\n"
            f"🔗 <a href='{url}'>Watch here</a>\n\n"
            f"#UpcomingAnime"
        )

        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            try:
                if image:
                    await bot.send_photo(
                        chat_id=str(chat_id).strip(),
                        photo=image,
                        caption=caption,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=str(chat_id).strip(),
                        text=caption,
                        parse_mode="HTML"
                    )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error sending release to {chat_id}]: {e}")

# Add this to your scheduler loop (for daily auto-posts)
async def auto_notify_daily(bot, CHANNEL_IDS):
    now = datetime.utcnow()
    next_run_time = now.replace(hour=10, minute=0, second=0, microsecond=0)  # For example, run every day at 10:00 AM UTC
    if now > next_run_time:
        next_run_time += timedelta(days=1)

    # Sleep until the next scheduled time
    await asyncio.sleep((next_run_time - now).total_seconds())
    await notify_releases(bot, CHANNEL_IDS, early=False)

    # Set up to repeat the process every 24 hours
    while True:
        await asyncio.sleep(86400)  # Sleep for 24 hours
        await notify_releases(bot, CHANNEL_IDS, early=False)

# Integrate into your main.py or bot initialization
async def on_start(bot, CHANNEL_IDS):
    # Start the auto-posting task
    asyncio.create_task(auto_notify_daily(bot, CHANNEL_IDS))
