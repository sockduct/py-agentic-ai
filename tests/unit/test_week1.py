from abc import ABC
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.models import Currency, Expense, ExpenseCategory
from expenses_ai_agent.storage.repo import ExpenseRepository, InMemoryExpenseRepository


class TestCurrencyEnum:
    """Tests for the Currency enumeration."""

    def test_currency_is_string_enum(self):
        """Currency should be a StrEnum so values work as strings."""
        assert Currency.EUR == "EUR"
        assert Currency.USD == "USD"
        assert str(Currency.EUR) == "EUR"

    def test_currency_has_required_values(self):
        """Currency enum must include at least these 10 common currencies."""
        required_currencies = [
            "EUR",
            "USD",
            "GBP",
            "JPY",
            "CHF",
            "CAD",
            "AUD",
            "CNY",
            "INR",
            "MXN",
        ]

        for code in required_currencies:
            assert hasattr(Currency, code), f"Currency.{code} is missing"
            assert Currency[code].value == code

    def test_currency_is_iterable(self):
        """Should be able to iterate over all currency values."""
        currencies = list(Currency)
        assert len(currencies) >= 10
        assert all(isinstance(c, Currency) for c in currencies)


class TestExpenseCategoryEnum:
    """Tests for the ExpenseCategory enumeration."""

    def test_category_is_string_enum(self):
        """ExpenseCategory should be a StrEnum so values work as strings."""
        assert ExpenseCategory.FOOD == "Food"
        assert ExpenseCategory.TRANSPORT == "Transport"
        assert str(ExpenseCategory.FOOD) == "Food"

    def test_category_has_required_values(self):
        """ExpenseCategory enum must include all 12 categories."""
        required = [
            "Food",
            "Transport",
            "Entertainment",
            "Shopping",
            "Health",
            "Bills",
            "Education",
            "Travel",
            "Services",
            "Gifts",
            "Investments",
            "Other",
        ]

        for name in required:
            assert name in [c.value for c in ExpenseCategory], (
                f"Category '{name}' is missing"
            )

    def test_category_is_iterable(self):
        """Should be able to iterate over all category values."""
        categories = list(ExpenseCategory)
        assert len(categories) == 12
        assert all(isinstance(c, ExpenseCategory) for c in categories)


class TestStorageExceptions:
    """Tests for custom storage exceptions."""

    def test_expense_not_found_error_exists(self):
        """ExpenseNotFoundError should be a custom exception."""
        error = ExpenseNotFoundError(123)
        assert isinstance(error, Exception)
        assert "123" in str(error)


class TestExpense:
    """Tests for the Expense model."""

    def test_expense_has_required_fields(self):
        """Expense must have all required fields for expense tracking."""
        expense = Expense(
            amount=Decimal("42.50"),
            currency=Currency.EUR,
            description="Lunch at restaurant",
        )

        assert hasattr(expense, "id")
        assert hasattr(expense, "amount")
        assert hasattr(expense, "currency")
        assert hasattr(expense, "description")
        assert hasattr(expense, "date")
        assert hasattr(expense, "category")

    def test_expense_amount_is_decimal(self):
        """Amount should use Decimal for financial precision."""
        expense = Expense(
            amount=Decimal("19.99"),
            currency=Currency.USD,
        )

        assert isinstance(expense.amount, Decimal)
        assert expense.amount == Decimal("19.99")

    def test_expense_currency_default(self):
        """Currency should default to EUR if not specified."""
        expense = Expense(amount=Decimal("10.00"))

        assert expense.currency == Currency.EUR

    def test_expense_date_defaults_to_now(self):
        """Date should default to current UTC time."""
        before = datetime.now(timezone.utc)
        expense = Expense(amount=Decimal("5.00"))
        after = datetime.now(timezone.utc)

        assert expense.date is not None
        assert before <= expense.date <= after or (after - before).total_seconds() < 2

    def test_expense_str_representation(self):
        """Expense __str__ should provide a readable summary."""
        expense = Expense(
            amount=Decimal("25.00"),
            currency=Currency.GBP,
            description="Book purchase",
        )

        result = str(expense)
        assert "25" in result
        assert "GBP" in result

    def test_expense_create_class_method(self):
        """Expense.create() should be a convenient factory method."""
        expense = Expense.create(
            amount=Decimal("99.99"),
            currency=Currency.USD,
            description="New headphones",
            category=ExpenseCategory.SHOPPING,
        )

        assert isinstance(expense, Expense)
        assert expense.amount == Decimal("99.99")
        assert expense.currency == Currency.USD
        assert expense.description == "New headphones"
        assert expense.category == ExpenseCategory.SHOPPING

    def test_expense_optional_telegram_user_id(self):
        """Expense should support optional telegram_user_id for multiuser."""
        expense = Expense(
            amount=Decimal("10.00"),
            telegram_user_id=12345,
        )

        assert expense.telegram_user_id == 12345

        expense_no_user = Expense(amount=Decimal("10.00"))
        assert expense_no_user.telegram_user_id is None


class TestRepositoryAbstractBase:
    """Tests to verify abstract base class is properly defined."""

    def test_expense_repository_is_abstract(self):
        """ExpenseRepository should be an abstract base class."""
        assert issubclass(ExpenseRepository, ABC)

        with pytest.raises(TypeError):
            ExpenseRepository()

    def test_inmemory_repo_inherits_from_abstract(self):
        """In-memory repository should implement the abstract base class."""
        assert issubclass(InMemoryExpenseRepository, ExpenseRepository)


class TestInMemoryExpenseRepository:
    """Tests for the in-memory expense repository."""

    @pytest.fixture
    def repo(self):
        return InMemoryExpenseRepository()

    @pytest.fixture
    def sample_expense(self):
        return Expense(
            amount=Decimal("42.50"),
            currency=Currency.EUR,
            description="Test expense",
        )

    def test_add_expense_assigns_id(self, repo, sample_expense):
        """Adding an expense should assign an auto-incremented ID."""
        assert sample_expense.id is None

        repo.add(sample_expense)

        assert sample_expense.id is not None
        assert sample_expense.id >= 1

    def test_print_repo(self, repo, sample_expense):
        """Should print out the repo and its expense."""
        repo.add(sample_expense)

        output = str(repo)
        test_output = f"{repo.__class__.__name__}(1 expense(s)):\n1: {sample_expense}\n"
        assert output == test_output

    def test_get_expense_by_id(self, repo, sample_expense):
        """Should retrieve expense by ID."""
        repo.add(sample_expense)

        result = repo.get(sample_expense.id)

        assert result is not None
        assert result.amount == Decimal("42.50")

    def test_get_nonexistent_returns_none(self, repo):
        """Getting a non-existent expense should return None."""
        result = repo.get(999)
        assert result is None

    def test_update_expense_by_id(self, repo, sample_expense):
        """Should update expense by ID."""
        repo.add(sample_expense)
        sample_expense.category = ExpenseCategory.OTHER
        repo.update(sample_expense)

        result = repo.get(sample_expense.id)

        assert result is not None
        assert result.category == ExpenseCategory.OTHER

    def test_update_nonexistent_expense_raises(self, repo, sample_expense):
        """Updating a non-existent expense should raise ExpenseNotFoundError."""
        with pytest.raises(ExpenseNotFoundError):
            repo.update(sample_expense)

    def test_list_all_expenses(self, repo):
        """Should list all expenses."""
        repo.add(Expense(amount=Decimal("10.00"), currency=Currency.EUR))
        repo.add(Expense(amount=Decimal("20.00"), currency=Currency.USD))

        expenses = repo.get_all()

        assert len(expenses) == 2

    def test_list_all_zero_expenses(self, repo):
        """Listing expenses on an empty repository should return an empty list."""
        expenses = repo.get_all()
        assert expenses == []

    def test_delete_expense(self, repo, sample_expense):
        """Should be able to delete an expense."""
        repo.add(sample_expense)
        expense_id = sample_expense.id

        repo.delete(expense_id)

        assert repo.get(expense_id) is None

    def test_delete_nonexistent_raises(self, repo):
        """Deleting a non-existent expense should raise ExpenseNotFoundError."""
        with pytest.raises(ExpenseNotFoundError):
            repo.delete(999)

    def test_search_by_category(self, repo):
        """Should be able to search expenses by category."""
        repo.add(
            Expense(
                amount=Decimal("10.00"),
                currency=Currency.EUR,
                category=ExpenseCategory.FOOD,
            )
        )
        repo.add(
            Expense(
                amount=Decimal("20.00"),
                currency=Currency.EUR,
                category=ExpenseCategory.FOOD,
            )
        )
        repo.add(
            Expense(
                amount=Decimal("30.00"),
                currency=Currency.EUR,
                category=ExpenseCategory.TRANSPORT,
            )
        )

        food_expenses = repo.search_by_category(ExpenseCategory.FOOD)

        assert len(food_expenses) == 2
        assert all(e.category == ExpenseCategory.FOOD for e in food_expenses)
