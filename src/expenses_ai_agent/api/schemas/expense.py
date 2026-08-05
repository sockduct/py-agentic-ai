# from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from expenses_ai_agent.storage.models import Currency, ExpenseCategory


class ExpenseClassifyRequest(BaseModel):
    """Request body for expense classification."""

    description: str = Field(
        ...,  # Required field
        min_length=3,
        max_length=500,
        examples=["Coffee at Starbucks $5.50"],
    )

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        # sourcery skip: reintroduce-else, swap-if-else-branches, use-named-expression
        stripped = v.strip()
        if not stripped:
            raise ValueError("description cannot be empty or whitespace")

        return stripped


class ExpenseClassifyResponse(BaseModel):
    """Response body after expense classification."""

    id: int
    category: ExpenseCategory
    amount: Decimal
    currency: Currency
    confidence: float
    # created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseResponse(BaseModel):
    """Single expense in a list."""

    id: int | None
    amount: Decimal
    currency: Currency
    category: ExpenseCategory | None
    description: str | None
    telegram_user_id: int | None
    # created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    """Paginated list of expenses."""

    items: list[ExpenseResponse]
    total: int
    page: int
    page_size: int
