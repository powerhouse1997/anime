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


def get_live_commentary():
    try:
        url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{MATCH_ID}/comm"
        headers = {
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        comm_list = data.get("comm_lines", [])
        if not comm_list:
            return "No live commentary available."

        latest_comm = comm_list[0]
        over = latest_comm.get("over_number", "")
        comm_text = latest_comm.get("comm", "No text")

        return f"<b>Live Commentary</b>\nOver: <i>{over}</i>\n{comm_text}"
    except Exception as e:
        print(f"[get_live_commentary] Error: {e}")
        return "Failed to fetch live commentary."


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