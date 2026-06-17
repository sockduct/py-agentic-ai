# Standard Library Imports:
from abc import ABC, abstractmethod

from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError

# Package Imports:
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
