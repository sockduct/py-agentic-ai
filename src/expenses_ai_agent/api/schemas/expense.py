# from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


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
        if stripped := v.strip():
            return stripped
        else:
            raise ValueError("description cannot be empty or whitespace")


class ExpenseClassifyResponse(BaseModel):
    """Response body after expense classification."""

    id: int
    category: str
    amount: Decimal
    currency: str
    confidence: float
    # created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseResponse(BaseModel):
    """Single expense in a list."""

    id: int | None
    amount: Decimal
    currency: str
    category: str | None
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
