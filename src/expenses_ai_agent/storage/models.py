from datetime import datetime, timezone
from decimal import Decimal
from enum import UNIQUE, StrEnum, verify

from sqlmodel import Field, SQLModel

TWOPLACES = Decimal("0.01")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@verify(UNIQUE)
class Currency(StrEnum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    CNY = "CNY"
    INR = "INR"
    MXN = "MXN"


DEFAULT_CURRENCY: Currency = Currency.EUR


def _currency_symbol(currency: Currency = DEFAULT_CURRENCY) -> str:
    symbols = {
        Currency.EUR: "€",
        Currency.USD: "$",
        Currency.GBP: "£",
        Currency.JPY: "¥",
        Currency.CHF: "Fr.",
        Currency.CAD: "$",
        Currency.AUD: "$",
        Currency.CNY: "¥",
        Currency.INR: "₹",
        Currency.MXN: "$",
    }
    return symbols.get(currency, DEFAULT_CURRENCY)


@verify(UNIQUE)
class ExpenseCategory(StrEnum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    HEALTH = "Health"
    BILLS = "Bills"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    SERVICES = "Services"
    GIFTS = "Gifts"
    INVESTMENTS = "Investments"
    OTHER = "Other"


class Expense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    amount: Decimal
    currency: Currency = DEFAULT_CURRENCY
    description: str | None = None
    date: datetime = Field(default_factory=_utc_now)
    category: ExpenseCategory | None = None
    telegram_user_id: int | None = None

    def __repr__(self) -> str:
        return (
            f"Expense(id={self.id}, amount={self.amount}, currency={self.currency}, "
            f"description={self.description}, date={self.date.isoformat()}, "
            f"category={self.category}, telegram_user_id={self.telegram_user_id})"
        )

    def __str__(self) -> str:
        return (
            f"{_currency_symbol(self.currency)}{self.amount.quantize(TWOPLACES)} "
            f"[{self.currency}] - {self.description or 'No description'} "
            f"({self.category or 'Uncategorized'}) on "
            f"{self.date.strftime('%a %b %d %Y, %I:%M%p %Z')}"
        )

    @classmethod
    def create(
        cls,
        amount: Decimal = Decimal("0.00"),
        currency: Currency = DEFAULT_CURRENCY,
        description: str | None = None,
        date: datetime | None = None,
        category: ExpenseCategory | None = None,
        telegram_user_id: int | None = None,
    ) -> "Expense":
        """Factory method to create an Expense with default values."""
        return cls(
            amount=amount,
            currency=currency,
            description=description,
            date=date if date is not None else _utc_now(),
            category=category,
            telegram_user_id=telegram_user_id,
        )
