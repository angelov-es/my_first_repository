from aiogram.fsm.state import StatesGroup, State

class AddPlanStates(StatesGroup):
    waiting_for_name = State()
    choosing_day = State()
    choosing_muscle_group_or_rest = State()

class AddExerciseStates(StatesGroup):
    waiting_for_exercise_name = State()
    waiting_for_weight = State()
    waiting_for_sets = State()
    waiting_for_reps = State()

class ViewPlanStates(StatesGroup):
    choosing_plan = State()
    choosing_day = State()
    choosing_muscle = State()