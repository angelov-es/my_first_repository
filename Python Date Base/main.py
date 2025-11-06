import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from db import SessionLocal, init_db, get_or_create_user
from models import User, WorkoutPlan, WorkoutDay, MuscleGroup, Exercise
from states import AddPlanStates, AddExerciseStates
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Установи BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

init_db()

DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MUSCLE_GROUPS = ["Грудь", "Спина", "Ноги", "Руки", "Плечи", "Пресс"]

# ------------------ Меню команд ------------------
COMMANDS_MENU = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="/add_plan"), types.KeyboardButton(text="/plans")],
        [types.KeyboardButton(text="/delete_plan"), types.KeyboardButton(text="/help")],
        [types.KeyboardButton(text="/add_exercise")]
    ],
    resize_keyboard=True
)

# ------------------ Команды ------------------
@dp.message(Command(commands=["start"]))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    db = SessionLocal()
    user = get_or_create_user(db, message.from_user.id, message.from_user.full_name)
    db.close()
    await message.answer(f"Привет, {user.name}! Я твой бот-дневник 💪", reply_markup=COMMANDS_MENU)

@dp.message(Command(commands=["help"]))
async def help_handler(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "/start - Запуск бота\n"
        "/add_plan - Создать новый план\n"
        "/plans - Просмотреть или редактировать планы\n"
        "/delete_plan - Удалить план\n"
        "/add_exercise - Добавить упражнения"
    )
    await message.answer(text, reply_markup=COMMANDS_MENU)

# ------------------ /add_plan ------------------
@dp.message(Command(commands=["add_plan"]))
async def add_plan(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите название нового плана:", reply_markup=COMMANDS_MENU)
    await state.set_state(AddPlanStates.waiting_for_name)

@dp.message(AddPlanStates.waiting_for_name)
async def create_plan(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if user:
        plan = WorkoutPlan(name=message.text, user=user)
        db.add(plan)
        db.commit()
        await message.answer(f"План '{plan.name}' создан! Теперь выберите день недели:", reply_markup=COMMANDS_MENU)

        buttons = [[types.InlineKeyboardButton(text=day, callback_data=f"day_{day}")] for day in DAYS_OF_WEEK]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Выберите день:", reply_markup=keyboard)

        await state.update_data(plan_id=plan.id)
        await state.set_state(AddPlanStates.choosing_day)
    db.close()

# ------------------ Выбор дня ------------------
@dp.callback_query(lambda c: c.data.startswith("day_"), AddPlanStates.choosing_day)
async def choose_day(callback: types.CallbackQuery, state: FSMContext):
    day_name = callback.data.split("_")[1]
    data = await state.get_data()
    plan_id = data.get("plan_id")
    db = SessionLocal()
    day = WorkoutDay(plan_id=plan_id, day_of_week=day_name)
    db.add(day)
    db.commit()
    await state.update_data(day_id=day.id)

    buttons = [[types.InlineKeyboardButton(text=g, callback_data=f"muscle_{g}")] for g in MUSCLE_GROUPS]
    buttons.insert(0, [types.InlineKeyboardButton(text="Отдых", callback_data="rest")])
    buttons.append([types.InlineKeyboardButton(text="Готово", callback_data="done")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(f"{day_name}: Выберите группы мышц или 'Отдых':", reply_markup=keyboard)
    await state.set_state(AddPlanStates.choosing_muscle_group_or_rest)
    await callback.answer()
    db.close()

# ------------------ Выбор группы мышц или отдыха ------------------
@dp.callback_query(lambda c: c.data.startswith("muscle_") or c.data in ["rest", "done"], AddPlanStates.choosing_muscle_group_or_rest)
async def choose_muscle_or_rest(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data
    data = await state.get_data()
    day_id = data.get("day_id")
    db = SessionLocal()

    if choice == "rest":
        day = db.query(WorkoutDay).filter(WorkoutDay.id == day_id).first()
        day.note = "Отдых"
        db.commit()
        await callback.message.edit_text(f"{day.day_of_week}: Отдых записан ✅", reply_markup=COMMANDS_MENU)
        await state.clear()
    elif choice == "done":
        await callback.message.edit_text("Выбор групп мышц завершён ✅", reply_markup=COMMANDS_MENU)
        await state.clear()
    elif choice.startswith("muscle_"):
        muscle_name = choice.split("_")[1]
        exists = db.query(MuscleGroup).filter(MuscleGroup.day_id == day_id, MuscleGroup.name == muscle_name).first()
        if not exists:
            muscle = MuscleGroup(name=muscle_name, day_id=day_id)
            db.add(muscle)
            db.commit()
            await callback.message.answer(f"{muscle_name} добавлена ✅", reply_markup=None)
            await state.update_data(muscle_id=muscle.id)
        else:
            await callback.message.answer(f"{muscle_name} уже добавлена", reply_markup=None)
    await callback.answer()
    db.close()

# ------------------ /plans ------------------
@dp.message(Command(commands=["plans"]))
async def list_plans(message: types.Message, state: FSMContext):
    await state.clear()
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user or not user.plans:
        await message.answer("У тебя пока нет планов.", reply_markup=COMMANDS_MENU)
        db.close()
        return

    buttons = [[types.InlineKeyboardButton(text=p.name, callback_data=f"viewplan_{p.id}")] for p in user.plans]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите план для просмотра:", reply_markup=keyboard)
    db.close()

# ------------------ Просмотр выбранного плана ------------------
@dp.callback_query(lambda c: c.data.startswith("viewplan_"))
async def view_plan_callback(callback: types.CallbackQuery):
    plan_id = int(callback.data.split("_")[1])
    db = SessionLocal()
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        await callback.message.edit_text("План не найден ❌", reply_markup=None)
        db.close()
        await callback.answer()
        return

    # Формируем текст с днями и группами мышц
    text = f"План: {plan.name}\n\n"
    for day in plan.days:
        text += f"{day.day_of_week}: "
        if day.note == "Отдых":
            text += "Отдых\n"
        elif day.muscle_groups:
            muscles = ", ".join([mg.name for mg in day.muscle_groups])
            text += f"{muscles}\n"
        else:
            text += "Нет групп мышц\n"

    await callback.message.edit_text(text, reply_markup=None)
    db.close()
    await callback.answer()

# ------------------ /delete_plan ------------------
@dp.message(Command(commands=["delete_plan"]))
async def delete_plan(message: types.Message, state: FSMContext):
    await state.clear()
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user or not user.plans:
        await message.answer("У тебя пока нет планов для удаления.", reply_markup=COMMANDS_MENU)
        db.close()
        return

    buttons = [[types.InlineKeyboardButton(text=p.name, callback_data=f"delete_{p.id}")] for p in user.plans]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите план для удаления:", reply_markup=keyboard)
    db.close()

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_plan_callback(callback: types.CallbackQuery):
    plan_id = int(callback.data.split("_")[1])
    db = SessionLocal()
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if plan:
        db.delete(plan)
        db.commit()
        await callback.message.edit_text(f"План '{plan.name}' удалён ✅", reply_markup=None)
    else:
        await callback.message.edit_text("План не найден", reply_markup=None)
    db.close()
    await callback.answer()

# ------------------ Запуск бота ------------------
async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
