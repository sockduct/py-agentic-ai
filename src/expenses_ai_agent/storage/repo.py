from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from itertools import groupby
from threading import Lock
from types import TracebackType
from typing import ClassVar, final
from warnings import warn

from sqlalchemy import func
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine, select

from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.models import (
    Currency,
    Expense,
    ExpenseCategory,
    UserPreference,
)


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
        """Retrieve expenses by a defined category."""
        ...

    @abstractmethod
    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Retrieve expenses by a datetime range."""
        ...

    @abstractmethod
    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Retrieve expenses by a specified user id."""
        ...

    @abstractmethod
    def get_monthly_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve monthly totals by a specified user id."""
        ...

    @abstractmethod
    def get_category_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve defined category totals by a specified user id."""
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
        """Retrieve expenses by a defined category."""
        return [
            expense
            for expense in self._expenses.values()
            if expense.category == category
        ]

    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Retrieve expenses by a datetime range."""
        return [
            expense
            for expense in self._expenses.values()
            if start <= expense.date < end
        ]

    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Retrieve expenses by a specified user id."""
        return [
            expense
            for expense in self._expenses.values()
            if expense.telegram_user_id == telegram_user_id
        ]

    def _sum_group_by_x(
        self,
        sort_field: str,
        group_attr: str,
        filter_val: int,
        *,
        filter_field: str = "telegram_user_id",
        group_attr_args: tuple = (),
    ) -> dict[str, Decimal]:
        """Helper function:
        * Sort expenses by sort_field, optionally filter by filter_field (inclusive)
        * Group expenses by group_attr
        * Return dict with key of sort_field.group_attr and value of
          sum(expense.amount) of each group
        """
        values = sorted(
            (
                val
                for val in self._expenses.values()
                if getattr(val, filter_field) == filter_val
            ),
            key=lambda val: getattr(val, sort_field),
        )
        grouped_values = {
            key: list(group)
            for key, group in groupby(
                values,
                key=lambda val: getattr(getattr(val, sort_field), group_attr)(
                    *group_attr_args
                ),
            )
        }
        return {
            key: sum(val.amount for val in values)
            for key, values in grouped_values.items()
        }

    def get_monthly_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve monthly totals by a specified user id.

        Group expenses for the specified telegram_user_id by expense.date.strftime("%Y-%m")
        Sum expense.amount for all items in each group (YYYY-MM)
        """
        return self._sum_group_by_x(
            sort_field="date",
            group_attr="strftime",
            filter_val=telegram_user_id,
            group_attr_args=("%Y-%m",),
        )

    def get_category_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve defined category totals by a specified user id.

        Group by expense.category (category name as string key)
        Sum expense.amount for all items in each category
        """
        return self._sum_group_by_x(
            sort_field="category", group_attr="__str__", filter_val=telegram_user_id
        )


@final
class DBExpenseRepo(ExpenseRepository):
    """Support CRUD and search for selected database."""

    _owned_instance: ClassVar[DBExpenseRepo | None] = None
    _owned_db_url: ClassVar[URL | None] = None
    _singleton_lock: ClassVar[Lock] = Lock()

    _engine: Engine
    _session: Session | None
    _owns_session: bool
    _open: bool

    def __new__(cls, db_url: str, session: Session | None = None) -> DBExpenseRepo:
        if session is not None:
            return super().__new__(cls)

        requested_url = make_url(db_url)
        owner = DBExpenseRepo

        with owner._singleton_lock:
            if owner._owned_instance is not None:
                if requested_url != owner._owned_db_url:
                    active_url = cls._safe_url(owner._owned_db_url)
                    new_url = cls._safe_url(requested_url)
                    raise RuntimeError(
                        "DBExpenseRepo already has an active instance for "
                        f"{active_url}; cannot initialize one for {new_url}. "
                        "Close the active DBExpenseRepo first."
                    )
                return owner._owned_instance

            instance = super().__new__(cls)
            engine = create_engine(requested_url)
            try:
                SQLModel.metadata.create_all(
                    engine
                )  # ensures the table exists in production
            except Exception:
                engine.dispose()
                raise

            instance._engine = engine
            instance._session = None
            instance._owns_session = True
            instance._open = True
            owner._owned_instance = instance
            owner._owned_db_url = requested_url
            return instance

    def __init__(self, db_url: str, session: Session | None = None) -> None:
        if session is None:
            return

        self._session = session
        self._owns_session = False
        self._open = True

    @staticmethod
    def _safe_url(db_url: URL | None) -> str:
        if db_url is None:
            return "unknown"
        return db_url.render_as_string(hide_password=True)

    def __enter__(self) -> DBExpenseRepo:
        warn(
            f"Context manager protocol is deprecated for {self.__class__.__name__} "
            "- call close() explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._require_open()
        if not self._owns_session:
            raise RuntimeError("Cannot manage external session!")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def __len__(self) -> int:
        self._require_open()
        statement = select(func.count()).select_from(Expense)
        if self._owns_session:
            with Session(self._engine) as session:
                return session.exec(statement).one()
        assert self._session is not None
        return self._session.exec(statement).one()

    def __repr__(self) -> str:
        db_url: object
        if self._owns_session and hasattr(self._engine, "url"):
            db_url = self._engine.url
            state = "open" if self.is_open() else "closed"
        elif self._session is not None and self._session.bind is not None:
            db_url = getattr(self._session.bind, "url", "unknown")
            state = "injected" if self.is_open() else "closed"
        else:
            db_url = "unknown"
            state = "unknown"

        return f"{self.__class__.__name__}(db_url={db_url}): {state}"

    def __str__(self) -> str:
        if not self.is_open():
            return "Database connection is closed."

        try:
            return "\n".join(
                f"{rownum}: {element}"
                for rownum, element in enumerate(self.get_all(), start=1)
            )
        except SQLAlchemyError:
            if self._owns_session:
                return "Unable to retrieve data from the database."
            return "Unable to access external session."

    def is_open(self) -> bool:
        if not self._open:
            return False
        if not self._owns_session:
            return True
        return self is DBExpenseRepo._owned_instance

    def _require_open(self) -> None:
        if not self.is_open():
            self._open = False
            raise RuntimeError("DBExpenseRepo is closed.")

    def close(self) -> None:
        if not self._open:
            return

        if not self._owns_session:
            self._open = False
            return

        owner = DBExpenseRepo
        with owner._singleton_lock:
            if self is not owner._owned_instance:
                self._open = False
                return

            self._engine.dispose()
            self._open = False
            owner._owned_instance = None
            owner._owned_db_url = None

    def add(self, expense: Expense) -> None:
        """Add an expense to the repository."""
        self._require_open()

        if self._owns_session:
            with Session(self._engine) as session:
                session.add(expense)
                session.commit()
                session.refresh(expense)
        else:
            assert self._session is not None
            self._session.add(expense)
            self._session.commit()
            self._session.refresh(expense)

    def update(self, expense: Expense) -> None:
        """Update an expense in the repository."""
        self._require_open()

        if not self._owns_session:
            assert self._session is not None
            if expense.id is None or self._session.get(Expense, expense.id) is None:
                raise ExpenseNotFoundError(
                    f"Expense with ID {expense.id} not found for update."
                )
            self._session.merge(expense)
            self._session.commit()
            return

        with Session(self._engine) as session:
            if expense.id is None or session.get(Expense, expense.id) is None:
                raise ExpenseNotFoundError(
                    f"Expense with ID {expense.id} not found for update."
                )
            session.merge(expense)
            session.commit()

    def get(self, expense_id: int) -> Expense | None:
        """Retrieve an expense by its ID."""
        self._require_open()

        if not self._owns_session:
            assert self._session is not None
            return self._session.get(Expense, expense_id)
        with Session(self._engine) as session:
            return session.get(Expense, expense_id)

    def get_all(self) -> list[Expense]:
        """Retrieve all expenses."""
        self._require_open()

        statement = select(Expense)
        if not self._owns_session:
            assert self._session is not None
            return list(self._session.exec(statement))
        with Session(self._engine) as session:
            return list(session.exec(statement))

    def delete(self, expense_id: int) -> None:
        """Remove an expense by its ID."""
        self._require_open()

        if not self._owns_session:
            assert self._session is not None
            expense = self._session.get(Expense, expense_id)
            if expense is None:
                raise ExpenseNotFoundError(f"Expense with ID {expense_id} not found.")
            self._session.delete(expense)
            self._session.commit()
            return

        with Session(self._engine) as session:
            expense = session.get(Expense, expense_id)
            if expense is None:
                raise ExpenseNotFoundError(f"Expense with ID {expense_id} not found.")
            session.delete(expense)
            session.commit()

    def search_by_category(self, category: ExpenseCategory) -> list[Expense]:
        """Retrieve expenses by a defined category."""
        self._require_open()

        statement = select(Expense).where(Expense.category == category)
        if not self._owns_session:
            assert self._session is not None
            return list(self._session.exec(statement))
        with Session(self._engine) as session:
            return list(session.exec(statement))

    def search_by_dates(self, start: datetime, end: datetime) -> list[Expense]:
        """Retrieve expenses by a datetime range."""
        self._require_open()

        statement = select(Expense).where(Expense.date >= start, Expense.date < end)
        if not self._owns_session:
            assert self._session is not None
            return list(self._session.exec(statement))
        with Session(self._engine) as session:
            return list(session.exec(statement))

    def list_by_user(self, telegram_user_id: int) -> list[Expense]:
        """Retrieve expenses by a specified user id."""
        self._require_open()

        statement = select(Expense).where(Expense.telegram_user_id == telegram_user_id)
        if not self._owns_session:
            assert self._session is not None
            return list(self._session.exec(statement))
        with Session(self._engine) as session:
            return list(session.exec(statement))

    def _sum_group_by_x(
        self,
        sort_field: str,
        group_attr: str,
        filter_val: int,
        *,
        group_attr_args: tuple = (),
    ) -> dict[str, Decimal]:
        """Helper function:
        Query the database via self.list_by_user(filter_val) and:
        * Sort expenses by sort_field
        * Group expenses by group_attr
        * Return dict with key of sort_field.group_attr and value of
          sum(expense.amount) of each group
        """
        values = sorted(
            self.list_by_user(filter_val), key=lambda val: getattr(val, sort_field)
        )
        grouped_values = {
            key: list(group)
            for key, group in groupby(
                values,
                key=lambda val: getattr(getattr(val, sort_field), group_attr)(
                    *group_attr_args
                ),
            )
        }
        return {
            key: sum(val.amount for val in values)
            for key, values in grouped_values.items()
        }

    def get_monthly_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve monthly totals by a specified user id.

        Group expenses for the specified telegram_user_id by expense.date.strftime("%Y-%m")
        Sum expense.amount for all items in each group (YYYY-MM)
        """
        return self._sum_group_by_x(
            sort_field="date",
            group_attr="strftime",
            filter_val=telegram_user_id,
            group_attr_args=("%Y-%m",),
        )

    def get_category_totals(self, telegram_user_id: int) -> dict[str, Decimal]:
        """Retrieve defined category totals by a specified user id.

        Group by expense.category (category name as string key)
        Sum expense.amount for all items in each category
        """
        return self._sum_group_by_x(
            sort_field="category", group_attr="__str__", filter_val=telegram_user_id
        )


class DBUserPreferenceRepo:
    def __init__(self, db_url: str, session: Session | None = None):
        self._owns_engine = session is None
        if session is None:
            self._engine = create_engine(db_url)
            SQLModel.metadata.create_all(self._engine)
            self.db = Session(self._engine)
        else:
            self._engine = None
            self.db = session

    def __enter__(self) -> "DBUserPreferenceRepo":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.db.close()
        if self._owns_engine and self._engine is not None:
            self._engine.dispose()

    def get_by_user_id(self, telegram_user_id: int) -> UserPreference | None:
        return self.db.exec(
            select(UserPreference).where(
                UserPreference.telegram_user_id == telegram_user_id
            )
        ).first()

    def upsert(self, telegram_user_id: int, currency: Currency) -> UserPreference:
        pref = self.get_by_user_id(telegram_user_id)
        if pref is None:
            pref = UserPreference(
                telegram_user_id=telegram_user_id, preferred_currency=currency
            )
            self.db.add(pref)
        else:
            pref.preferred_currency = currency
            pref.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(pref)
        return pref
