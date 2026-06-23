from datetime import datetime
from decimal import Decimal
from enum import UNIQUE, StrEnum, auto, verify
from typing import Any, cast

from decouple import config
from openai import OpenAI

from expenses_ai_agent.llms.base import MESSAGES
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse


@verify(UNIQUE)
class SortBy(StrEnum):
    CREATION = auto()
    NAME = auto()


class OpenAIAssistant:
    """LLM Provider for OpenAI models"""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        """Configure OpenAI API key and initialize OpenAI client."""
        self.model = model
        api_key = config("OPENAI_API_KEY", cast=str) if api_key is None else api_key
        self.client = OpenAI(api_key=api_key)

    def completion(self, messages: MESSAGES) -> ExpenseCategorizationResponse:
        """
        Call OpenAI new responses API leveraging structured output
        Use token counts to calculate cost
        """
        response = self.client.responses.parse(
            model=self.model,
            input=cast(Any, messages),
            text_format=ExpenseCategorizationResponse,
        )

        if response.output_parsed is None:
            raise ValueError("Failed to parse response from OpenAI.")

        expcat_resp = response.output_parsed

        if response.usage:
            cost = self.calculate_cost(
                response.usage.input_tokens,
                response.usage.output_tokens,
                cached_prompt_tokens=response.usage.input_tokens_details.cached_tokens,
            )

            expcat_resp.cost = cost

        return expcat_resp

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        *,
        cached_prompt_tokens: int = 0,
    ) -> Decimal:
        """
        Assuming gpt-4o-mini for costs as of June 22, 2026
        * input tokens (prompt_tokens):       $0.15
        * cached input tokens:                $0.075
        * output tokens (completion_tokens):  $0.60
        """
        return (
            Decimal("0.15") * prompt_tokens
            + Decimal("0.075") * cached_prompt_tokens
            + Decimal("0.60") * completion_tokens
        ).quantize(Decimal("0.00"))

    def get_available_models(self, *, sort_by: SortBy = SortBy.NAME) -> list[str]:
        """Provide sorted list of available models with creation dates."""
        response = self.client.models.list()
        sort_key = "created" if sort_by == SortBy.CREATION else "id"
        output = []
        for model in sorted(response.data, key=lambda m: getattr(m, sort_key)):
            dt_str = datetime.fromtimestamp(model.created).strftime("%b %d, %Y")
            output.append(f"{model.id:40} created on {dt_str}")

        return output
