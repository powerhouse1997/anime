# main.py

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from bs4 import BeautifulSoup
import requests
import asyncio
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_BOT_TOKEN"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
active_chats = set()

def get_live_score(ipl_only=False):
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
        status_tag = match.find('div', class_='cb-text-live') or match.find('div', class_='cb-text-complete')

        if title_tag and score_tag:
            title = title_tag.text.strip()
            if ipl_only and "ipl" not in title.lower():
                continue
            score = score_tag.text.strip()
            status = status_tag.text.strip() if status_tag else ''
            result += f"<b>{title}</b>\n{score}\n<i>{status}</i>\n\n"

    return result or ("No IPL live matches right now." if ipl_only else "No live matches right now.")

def get_upcoming_matches():
    url = "https://www.cricbuzz.com/cricket-series/7607/indian-premier-league-2025/matches"
    response = requests.get(url)
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

@dp.message(F.text == "/start")
@dp.message(F.text == "/help")
async def start_handler(message: Message):
    await message.answer(
        "Welcome to the IPL Live Score Bot!\n\n"
        "Available commands:\n"
        "/score - All live matches\n"
        "/live - Only IPL live matches\n"
        "/upcoming - Upcoming IPL matches\n"
        "/stop - Stop auto updates"
    )

@dp.message(F.text == "/score")
async def score_handler(message: Message):
    active_chats.add(message.chat.id)
    score = get_live_score()
    await message.answer(score, parse_mode=ParseMode.HTML)

@dp.message(F.text == "/live")
async def live_handler(message: Message):
    ipl_score = get_live_score(ipl_only=True)
    await message.answer(ipl_score, parse_mode=ParseMode.HTML)

@dp.message(F.text == "/upcoming")
async def upcoming_handler(message: Message):
    matches = get_upcoming_matches()
    await message.answer(matches, parse_mode=ParseMode.HTML)

@dp.message(F.text == "/stop")
async def stop_handler(message: Message):
    if message.chat.id in active_chats:
        active_chats.remove(message.chat.id)
        await message.answer("You’ve been unsubscribed from auto score updates.")
    else:
        await message.answer("You're not subscribed.")

async def auto_send_scores():
    while True:
        if active_chats:
            score = get_live_score()
            for chat_id in active_chats:
                try:
                    await bot.send_message(chat_id, score, parse_mode=ParseMode.HTML)
                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}")
        await asyncio.sleep(60)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_send_scores())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())