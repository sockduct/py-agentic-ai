# Standard Library:
from enum import UNIQUE, StrEnum, verify

# 3rd-Party Libraries:
from sqlmodel import SQLModel


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


class Expense(SQLModel):
    pass


class ExpenseCategory(StrEnum):
    pass
