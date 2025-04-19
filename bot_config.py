import os
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token-here")
CHAT_IDS = os.getenv("CHAT_IDS", "your-chat-id").split(",")
PINNABLE_ID = os.getenv("PIN_ID", CHAT_IDS[0])

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
