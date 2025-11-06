from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import AddPlanStates
from db import SessionLocal
from models import User, WorkoutPlan

async def register_plan_handlers(dp):

    @dp.message(Command(commands=["add_plan"]))
    async def add_plan(message: types.Message, state: FSMContext):
        await message.answer("Введите название нового плана:")
        await state.set_state(AddPlanStates.waiting_for_name)

    @dp.message(AddPlanStates.waiting_for_name)
    async def create_plan(message: types.Message, state: FSMContext):
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if user:
            plan = WorkoutPlan(name=message.text, user=user)
            db.add(plan)
            db.commit()
            await message.answer(f"План '{plan.name}' создан!")
        else:
            await message.answer("Сначала используй /start")
        db.close()
        await state.clear()