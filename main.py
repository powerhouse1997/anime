import os
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Function to fetch live cricket scores
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
            return "No live matches found."

        result = ""
        for match in matches:
            team1 = match["team1"].get("name", "")
            team2 = match["team2"].get("name", "")
            match_desc = match.get("matchDesc", "")
            status = match.get("status", "")
            score = match.get("score", [])
            score_lines = [score.get("inningScore", "") for score in score if score.get("inningScore")]

            title = f"{team1} vs {team2} ({match_desc})"
            result += f"<b>{title}</b>\n" + "\n".join(score_lines) + f"\n<i>{status}</i>\n\n"

        return result if result else "No live matches right now."
    except Exception as e:
        print(f"[get_live_score] Error: {e}")
        return "Failed to fetch live scores."

# Command to get live score
@dp.message(F.text.in_({"/start", "/help"}))
async def start_handler(message: Message):
    await message.answer("Welcome to the Cricket Live Score Bot! Use /score to get live scores.")

@dp.message(F.text == "/score")
async def score_handler(message: Message):
    live_scores = get_live_score()
    await message.answer(live_scores)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)