from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field

from expenses_ai_agent.storage.models import Currency, ExpenseCategory


class ExpenseCategorizationResponse(BaseModel):
    """
    Structured output from expense classification.

    Field description - important:
    ----------------------------------------------------------------------------
    OpenAI's structured output passes the description to the LLM, which uses it
    to know what value to fill in. Without descriptions, the LLM may fill
    numeric fields with 0.
    """

    category: ExpenseCategory
    total_amount: Decimal = Field(
        description="Numeric amount extracted from the expense description"
    )
    currency: Currency = Field(
        description="Currency code from the description, default EUR"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    cost: Decimal = Field(
        default=Decimal("0"),
        description="Leave as 0 — set programmatically after the API call",
    )
    comments: str | None = None
    # lambda needed to pass tz arg - datetime.utcnow is deprecated:
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
