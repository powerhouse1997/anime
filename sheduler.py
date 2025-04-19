import aiohttp
import asyncio
import html
from datetime import datetime, timezone
from typing import List, Optional

ANILIST_API = "https://graphql.anilist.co"

ANILIST_QUERY = """
query {
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

# Fetch upcoming releases from Anilist
async def fetch_anilist_upcoming() -> List[dict]:
    now_timestamp = int(datetime.now(tz=timezone.utc).timestamp())
    variables = {"now": now_timestamp}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                ANILIST_API,
                json={"query": ANILIST_QUERY, "variables": variables},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    print(f"Anilist error: {response.status}")
                    return []

                data = await response.json()
                results = []

                for item in data["data"]["Page"]["airingSchedules"]:
                    title = item["media"]["title"]["romaji"]
                    episode = item["episode"]
                    url = item["media"]["siteUrl"]
                    image = item["media"]["coverImage"]["large"]
                    dt = datetime.fromtimestamp(item["airingAt"], tz=timezone.utc)
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M UTC")

                    results.append({
                        "title": title,
                        "episode": episode,
                        "airing_at": formatted_date,
                        "url": url,
                        "image": image
                    })

                return results

    except Exception as e:
        print(f"Error fetching from Anilist API: {e}")
        return []

# Send upcoming releases to Telegram
async def notify_releases(bot, CHANNEL_IDS, manual_chat_id: Optional[int] = None):
    releases = await fetch_anilist_upcoming()

    if not releases:
        msg = "😔 No upcoming anime episodes found."
        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            await bot.send_message(chat_id=str(chat_id).strip(), text=msg)
        return

    for release in releases:
        title = html.escape(release["title"])
        episode = html.escape(str(release["episode"]))
        airing_at = html.escape(release["airing_at"])
        url = html.escape(release["url"])
        image = release["image"]

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"📺 <b>Episode:</b> <code>{episode}</code>\n"
            f"🕒 <b>Airing:</b> <code>{airing_at}</code>\n"
            f"🔗 <a href=\"{url}\">View on Anilist</a>\n\n"
            f"#UpcomingAnime"
        )

        targets = [manual_chat_id] if manual_chat_id else CHANNEL_IDS
        for chat_id in targets:
            try:
                await bot.send_photo(
                    chat_id=str(chat_id).strip(),
                    photo=image,
                    caption=caption,
                    parse_mode="HTML"
                )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error sending to {chat_id}]: {e}")
