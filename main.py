# main.py

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from bs4 import BeautifulSoup
import requests
import asyncio
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Or paste your token directly for testing
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_live_score():
    url = 'https://www.cricbuzz.com/cricket-match/live-scores'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    matches = soup.find_all('div', class_='cb-mtch-lst cb-col cb-col-100 cb-tms-itm')
    if not matches:
        return "No live matches found."

    result = ""
    for match in matches:
        title_tag = match.find('a')
        score_tag = match.find('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr')
        status_tag = match.find('div', class_='cb-text-live')

        if title_tag and score_tag:
            title = title_tag.text.strip()
            score = score_tag.text.strip()
            status = status_tag.text.strip() if status_tag else ''
            result += f"<b>{title}</b>\n{score}\n<i>{status}</i>\n\n"
    return result or "No live matches right now."

@dp.message(F.text == "/start")
@dp.message(F.text == "/help")
async def start_handler(message: Message):
    await message.answer("Welcome to the IPL Live Score Bot!\nUse /score to get the latest match updates.")

@dp.message(F.text == "/score")
async def score_handler(message: Message):
    score = get_live_score()
    await message.answer(score, parse_mode=ParseMode.HTML)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
