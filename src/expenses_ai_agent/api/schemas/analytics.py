from decimal import Decimal

from pydantic import BaseModel

from expenses_ai_agent.storage.models import ExpenseCategory


class CategoryTotal(BaseModel):
    """Spending total for a category."""

    category: ExpenseCategory
    total: Decimal


class MonthlyTotal(BaseModel):
    """Spending total for a month."""

    month: str  # "2025-01"
    total: Decimal


class AnalyticsSummary(BaseModel):
    """Dashboard analytics data."""

    category_totals: list[CategoryTotal]
    monthly_totals: list[MonthlyTotal]
