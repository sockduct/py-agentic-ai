from decouple import config
from fastapi import APIRouter, Depends, Header
from sqlmodel import Session, create_engine

from expenses_ai_agent.storage.repo import DBExpenseRepo, ExpenseRepository

DATABASE_URL = "sqlite:///expenses.db"
engine = create_engine(DATABASE_URL)
router = APIRouter(prefix="/expenses", tags=["Expenses"])


def get_db_session():
    with Session(engine) as session:
        yield session


def get_expense_repo(session: Session = Depends(get_db_session)) -> ExpenseRepository:
    return DBExpenseRepo(db_url=DATABASE_URL, session=session)


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-ID")) -> int:
    if x_user_id is not None:
        return int(x_user_id)
    return config("DEFAULT_USER_ID", cast=int, default=12345)
