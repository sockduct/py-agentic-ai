# Standard Library:
from datetime import datetime, timezone
from decimal import Decimal

# Package Imports:
from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.models import Currency, Expense, ExpenseCategory


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
