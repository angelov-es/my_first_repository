from aiogram import types
from aiogram.filters import Command
from db import SessionLocal, get_or_create_user

async def register_start(dp):
    @dp.message(Command(commands=["start"]))
    async def start_handler(message: types.Message):
        db = SessionLocal()
        user = get_or_create_user(db, message.from_user.id, message.from_user.full_name)
        db.close()
        await message.answer(f"Привет, {user.name}! Я твой бот-дневник тренировок 💪")