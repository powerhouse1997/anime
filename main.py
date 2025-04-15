from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import asyncio
import requests
from bs4 import BeautifulSoup
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # or hardcode the token for testing

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

def get_live_score():
    url = 'https://www.cricbuzz.com/cricket-match/live-scores'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    matches = soup.find_all('div', class_='cb-mtch-lst cb-col cb-col-100 cb-tms-itm')
    if not matches:
        return "No live matches found."

    result = ""
    for match in matches:
        title = match.find('a').text.strip()
        status = match.find('div', class_='cb-text-live').text.strip() if match.find('div', class_='cb-text-live') else ''
        score = match.find('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr').text.strip()
        result += f"<b>{title}</b>\n{score}\n<i>{status}</i>\n\n"
    return result or "No live matches right now."

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Use /score to get IPL live scores.")

@dp.message_handler(commands=['score'])
async def send_score(message: types.Message):
    await message.answer(get_live_score(), parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)