from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, SQLModel, col, create_engine, select

from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.models import Expense, ExpenseCategory


class ExpenseRepository(ABC):
    """Abstract interface"""

    @abstractmethod
    def add(self, expense: Expense) -> None:
        """Add an expense to the repository."""
        ...

    @abstractmethod
    def update(self, expense: Expense) -> None:
        """Update an expense in the repository."""
        ...

    @abstractmethod
    def get(self, expense_id: int) -> Expense | None:
        """Retrieve an expense by its ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[Expense]:
        """Retrieve all expenses."""
        ...

    @abstractmethod
    def delete(self, expense_id: int) -> None:
        """Remove an expense by its ID."""
        ...

    @abstractmethod
    def search_by_category(self, category: ExpenseCategory) -> list[Expense]:
        """Search for expenses by defined categories."""
        ...

    @abstractmethod
    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Search for expenses by defined dates."""
        ...

    @abstractmethod
    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Search for expenses by defined user."""
        ...


class InMemoryExpenseRepository(ExpenseRepository):
    """Needs to support CRUD and search"""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id: int = 1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({len(self._expenses)} expense(s))"

    def __str__(self) -> str:
        output = f"{self.__repr__()}:\n"
        for element in self.get_all():
            output += f"{element.id}: {element}\n"
        return output

    def add(self, expense: Expense) -> None:
        """Add an expense to the repository."""
        expense.id = self._next_id
        self._expenses[self._next_id] = expense
        self._next_id += 1

    def update(self, expense: Expense) -> None:
        """Update an expense in the repository."""
        if expense.id is None or expense.id not in self._expenses:
            expense_id = str(expense.id) if expense.id is not None else "None"
            raise ExpenseNotFoundError(
                f"Expense with ID {expense_id} not found for update."
            )
        self._expenses[expense.id] = expense

    def get(self, expense_id: int) -> Expense | None:
        """Retrieve an expense by its ID."""
        return self._expenses.get(expense_id)

    def get_all(self) -> list[Expense]:
        """Retrieve all expenses."""
        return list(self._expenses.values())

    def delete(self, expense_id: int) -> None:
        """Remove an expense by its ID."""
        if expense_id not in self._expenses:
            raise ExpenseNotFoundError(f"Expense with ID {expense_id} not found.")
        del self._expenses[expense_id]

    def search_by_category(self, category: ExpenseCategory) -> list[Expense]:
        """Search for expenses by defined categories."""
        return [
            expense
            for expense in self._expenses.values()
            if expense.category == category
        ]

    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Search for expenses by defined dates."""
        return [
            expense
            for expense in self._expenses.values()
            if start <= expense.date <= end
        ]

    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Search for expenses by defined user."""
        return [
            expense
            for expense in self._expenses.values()
            if expense.telegram_user_id == telegram_user_id
        ]


class DBExpenseRepo(ExpenseRepository):
    """Support CRUD and search for selected database."""

    def __init__(self, db_url: str, session: Session | None = None) -> None:
        if session is not None:
            self._session = session
            self._owns_session = False
        else:
            engine = create_engine(db_url)
            SQLModel.metadata.create_all(
                engine
            )  # ensures the table exists in production
            self.session = Session(engine)
            self._owns_session = True

    def __repr__(self) -> str:
        statement = select(func.count()).select_from(Expense)
        count = self._session.exec(statement).one()
        return f"{self.__class__.__name__}({count} expense(s))"

    def __str__(self) -> str:
        output = f"{self.__repr__()}:\n"
        for rownum, element in enumerate(self.get_all(), start=1):
            output += f"{rownum}: {element}\n"
        return output

    def add(self, expense: Expense) -> None:
        """Add an expense to the repository."""
        self._session.add(expense)
        self._session.commit()
        self._session.refresh(expense)

    def update(self, expense: Expense) -> None:
        """Update an expense in the repository."""
        if expense.id is None or not self.get(expense.id):
            raise ExpenseNotFoundError(
                f"Expense with ID {expense.id} not found for update."
            )
        self.add(expense)

    def get(self, expense_id: int) -> Expense | None:
        """Retrieve an expense by its ID."""
        return self._session.get(Expense, expense_id)

    def get_all(self) -> list[Expense]:
        """Retrieve all expenses."""
        statement = select(Expense)
        return list(self._session.exec(statement))

    def delete(self, expense_id: int) -> None:
        """Remove an expense by its ID."""
        if not (expense := self.get(expense_id)):
            raise ExpenseNotFoundError(f"Expense with ID {expense_id} not found.")
        self._session.delete(expense)
        self._session.commit()

    def search_by_category(self, category: ExpenseCategory) -> list[Expense]:
        """Search for expenses by defined categories."""
        statement = select(Expense).where(Expense.category == category)
        return list(self._session.exec(statement))

    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Search for expenses by defined dates."""
        statement = select(Expense).where(col(Expense.date).between(start, end))
        return list(self._session.exec(statement))

    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Search for expenses by defined user."""
        statement = select(Expense).where(Expense.telegram_user_id == telegram_user_id)
        return list(self._session.exec(statement))
