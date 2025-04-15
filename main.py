import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

response = requests.get(url, headers=headers, timeout=10)
print(response.json())  # Inspect the raw JSON response

@dp.message(F.text.in_({"/start", "/help"}))
async def start_handler(message: Message):
    await message.answer("Welcome! Use /score to get live cricket scores.")

@dp.message(F.text == "/score")
async def score_handler(message: Message):
    await message.answer(get_live_score())

def get_live_score():
    try:
        headers = {
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        matches = data.get("matches", [])
        if not matches:
            return "No live matches right now."

        msg = ""
        for match in matches:
            team1 = match.get("team1", {}).get("name", "")
            team2 = match.get("team2", {}).get("name", "")
            desc = match.get("matchDesc", "")
            status = match.get("status", "")
            scores = match.get("score", [])
            score_lines = [s.get("inningScore", "") for s in scores if s.get("inningScore")]
            title = f"<b>{team1} vs {team2}</b> ({desc})"
            msg += f"{title}\n" + "\n".join(score_lines) + f"\n<i>{status}</i>\n\n"

        return msg.strip()
    except Exception as e:
        return f"Error fetching scores: {e}"

async def delete_webhook_first():
    print("Deleting existing webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted.")

async def main():
    await delete_webhook_first()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())