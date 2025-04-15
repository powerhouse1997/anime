import os
import asyncio
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
WEBHOOK_URL = os.getenv("DOMAIN", "https://your-app-name.up.railway.app") + "/webhook"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
active_chats = set()


def get_live_score(ipl_only=False):
    try:
        url = 'https://www.cricbuzz.com/cricket-match/live-scores'
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = soup.find_all('div', class_='cb-mtch-lst cb-col cb-col-100 cb-tms-itm')
        if not matches:
            return "No live matches found."

        result = ""
        found_ipl = False
        for match in matches:
            title_tag = match.find('a')
            score_tag = match.find('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr')
            status_tag = match.find('div', class_='cb-text-live') or match.find('div', class_='cb-text-complete')

            if title_tag and score_tag:
                title = title_tag.text.strip()
                if ipl_only and "ipl" not in title.lower():
                    continue
                if "ipl" in title.lower():
                    found_ipl = True
                score = score_tag.text.strip()
                status = status_tag.text.strip() if status_tag else ''
                result += f"<b>{title}</b>\n{score}\n<i>{status}</i>\n\n"

        if ipl_only and not found_ipl:
            return "No IPL live matches right now."
        return result or "No live matches right now."
    except Exception as e:
        print(f"[get_live_score] Error: {e}")
        return "Failed to fetch live scores."


def get_upcoming_matches():
    try:
        url = "https://www.cricbuzz.com/cricket-series/7607/indian-premier-league-2025/matches"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        match_blocks = soup.select("div.cb-col.cb-col-100.cb-bg-white.cbs-mtchs-tm")
        if not match_blocks:
            return "No upcoming IPL matches found."

        upcoming = []
        for block in match_blocks[:5]:
            teams = block.select_one("a.cb-text-link")
            date = block.select_one("div.schedule-date")
            if teams and date:
                upcoming.append(f"<b>{teams.text.strip()}</b>\n<i>{date.text.strip()}</i>")

        return "\n\n".join(upcoming) or "No upcoming IPL matches found."
    except Exception as e:
        print(f"[get_upcoming_matches] Error: {e}")
        return "Failed to fetch upcoming matches."


@dp.message(F.text.in_({"/start", "/help"}))
async def start_handler(message: Message):
    await message.answer(
        "Welcome to the IPL Live Score Bot!\n\n"
        "Commands:\n"
        "/score - All live matches\n"
        "/live - Only IPL live matches\n"
        "/upcoming - Upcoming IPL matches\n"
        "/stop - Stop auto updates"
    )


@dp.message(F.text == "/score")
async def score_handler(message: Message):
    active_chats.add(message.chat.id)
    score = get_live_score()
    await message.answer(score)


@dp.message(F.text == "/live")
async def live_handler(message: Message):
    ipl_score = get_live_score(ipl_only=True)
    await message.answer(ipl_score)


@dp.message(F.text == "/upcoming")
async def upcoming_handler(message: Message):
    matches = get_upcoming_matches()
    await message.answer(matches)


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
                score = get_live_score(ipl_only=True)
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