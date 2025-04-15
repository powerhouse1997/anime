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

@dp.message(F.text.in_({"/start", "/help"}))
async def start_handler(message: Message):
    await message.answer("Welcome! Use /score to get live cricket scores.")

@dp.message(F.text == "/score")
async def score_handler(message: Message):
    await message.answer(get_live_score())

import requests
import os

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Or set it directly if you're testing

def get_live_score():
    try:
        if not RAPIDAPI_KEY:
            return "API key not set. Please configure RAPIDAPI_KEY."

        headers = {
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
            "X-RapidAPI-Key": RAPIDAPI_KEY
        }
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"

        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        matches = data.get("matches", [])
        if not matches:
            return "No live matches right now."

        result = ""
        for match in matches[:3]:  # Limit to 3 matches
            team1 = match.get("team1", {}).get("name", "Team 1")
            team2 = match.get("team2", {}).get("name", "Team 2")
            desc = match.get("matchDesc", "Match")
            status = match.get("status", "Status Unknown")
            scores = match.get("score", [])
            score_lines = [s.get("inningScore", "") for s in scores if s.get("inningScore")]

            result += f"<b>{team1} vs {team2}</b> ({desc})\n"
            if score_lines:
                result += "\n".join(score_lines) + "\n"
            result += f"<i>{status}</i>\n\n"

        return result.strip() or "Live data not available."
    
    except Exception as e:
        return f"Error fetching score: {str(e)}"

async def delete_webhook_first():
    print("Deleting existing webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted.")

async def main():
    await delete_webhook_first()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

print(response.json())