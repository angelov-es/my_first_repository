from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    name = Column(String)
    plans = relationship("WorkoutPlan", back_populates="user")

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="plans")
    days = relationship("WorkoutDay", back_populates="plan")

class WorkoutDay(Base):
    __tablename__ = "workout_days"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    day_of_week = Column(String)  # "Пн", "Вт", ...
    note = Column(String)          # "Отдых" или пусто
    plan = relationship("WorkoutPlan", back_populates="days")
    muscle_groups = relationship("MuscleGroup", back_populates="day")

class MuscleGroup(Base):
    __tablename__ = "muscle_groups"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("workout_days.id"))
    name = Column(String)  # "Грудь", "Спина" ...
    day = relationship("WorkoutDay", back_populates="muscle_groups")
    exercises = relationship("Exercise", back_populates="muscle_group")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True)
    muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id"))
    name = Column(String)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    muscle_group = relationship("MuscleGroup", back_populates="exercises")
