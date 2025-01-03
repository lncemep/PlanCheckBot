# core.py
from aiogram import Bot, Dispatcher, Router
from config import comands  # Здесь у вас хранится BOT_TOKEN (comands='123456:ABC-...')

bot = Bot(token=comands)
dp = Dispatcher()
router = Router()