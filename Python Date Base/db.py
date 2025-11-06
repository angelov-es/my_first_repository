from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, WorkoutPlan, Exercise
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gym_journal.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_or_create_user(db, telegram_id, name=None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user