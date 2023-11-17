from os import getenv
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.enums import ParseMode

load_dotenv()

bot = Bot(getenv("BOT_TOKEN"), parse_mode=ParseMode.HTML)
