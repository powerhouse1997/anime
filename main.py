import os
import asyncio
import requests
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
WEBHOOK_URL = os.getenv("DOMAIN", "https://your-app-name.up.railway.app") + "/webhook"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "375989156amshe0be74b7c18e841p115957jsn6b270db10190")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
active_chats = set()

MATCH_ID = "41881"  # Example match ID, replace with dynamic if needed


def get_live_score(ipl_only=False):
    try:
        headers = {
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com",
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", "375989156amshe0be74b7c18e841p115957jsn6b270db10190")
        }
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        matches = data.get("matches", [])
        if not matches:
            return "No live matches found."

        result = ""
        found_ipl = False

        for match in matches:
            series_name = match.get("seriesName", "")
            team1 = match["team1"].get("name", "")
            team2 = match["team2"].get("name", "")
            match_desc = match.get("matchDesc", "")
            status = match.get("status", "")
            scores = match.get("score", [])

            score_lines = []
            for score in scores:
                team = score.get("teamId", "")
                inning = score.get("inningScore", "")
                if inning:
                    score_lines.append(inning)

            title = f"{team1} vs {team2} ({match_desc})"

            if ipl_only and "ipl" not in series_name.lower():
                continue
            if "ipl" in series_name.lower():
                found_ipl = True

            result += f"<b>{title}</b>\n" + "\n".join(score_lines) + f"\n<i>{status}</i>\n\n"

        if ipl_only and not found_ipl:
            return "No IPL live matches right now."

        return result or "No live matches right now."
    except Exception as e:
        print(f"[get_live_score] Error: {e}")
        return "Failed to fetch live scores."


@dp.message(F.text.in_({"/start", "/help"}))
async def start_handler(message: Message):
    await message.answer(
        "Welcome to the Cricket Live Score Bot!\n\n"
        "Commands:\n"
        "/score - Live commentary\n"
        "/stop - Stop auto updates"
    )


@dp.message(F.text == "/score")
async def score_handler(message: Message):
    active_chats.add(message.chat.id)
    score = get_live_commentary()
    await message.answer(score)


@dp.message(F.text == "/stop")
async def stop_handler(message: Message):
    if message.chat.id in active_chats:
        active_chats.remove(message.chat.id)
        await message.answer("You’ve been unsubscribed from auto score updates.")
    else:
        await message.answer("You're not subscribed.")


async def auto_send_scores():
    while True:
        try:
            if active_chats:
                score = get_live_commentary()
                for chat_id in active_chats:
                    try:
                        await bot.send_message(chat_id, score)
                    except Exception as e:
                        print(f"Failed to send to {chat_id}: {e}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"[auto_send_scores] Loop error: {e}")
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await bot.set_webhook(WEBHOOK_URL)
        asyncio.create_task(auto_send_scores())
    except Exception as e:
        print(f"[lifespan] Error setting webhook or starting task: {e}")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        print(f"[webhook] Error: {e}")
        return {"ok": False}