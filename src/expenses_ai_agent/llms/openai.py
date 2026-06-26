from datetime import datetime
from decimal import Decimal
from enum import UNIQUE, StrEnum, auto, verify
from typing import cast

from decouple import config
from openai import OpenAI
from openai.types.responses import ResponseInputParam

from expenses_ai_agent.llms.base import MESSAGES
from expenses_ai_agent.llms.exceptions import ResponseError
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse

# For gpt-4o-mini as of June 24, 2026:
INPUT_RATE = Decimal("0.15") / 1_000_000
CACHED_INPUT_RATE = Decimal("0.075") / 1_000_000
OUTPUT_RATE = Decimal("0.60") / 1_000_000


@verify(UNIQUE)
class SortBy(StrEnum):
    CREATION = auto()
    NAME = auto()


class OpenAIAssistant:
    """LLM Provider for OpenAI models"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        *,
        store: bool = False,
    ) -> None:
        """Configure OpenAI API key and initialize OpenAI client."""
        self.model = model
        self.store = store  # Should OpenAI retain responses (enable if needed)
        api_key = config("OPENAI_API_KEY") if api_key is None else api_key
        self.client = OpenAI(api_key=api_key)

    def completion(self, messages: MESSAGES) -> ExpenseCategorizationResponse:
        """
        Call OpenAI new responses API leveraging structured output
        Use token counts to calculate cost
        """
        response = self.client.responses.parse(
            model=self.model,
            store=self.store,
            input=cast(ResponseInputParam, messages),
            text_format=ExpenseCategorizationResponse,
        )

        if response.output_parsed is None:
            output = f"status={response.status}"
            # Should see error populated for response failure case:
            if response.error:
                output += f", error={response.error}"
            # Should see incomplete_details populated for things like exceeding
            # max_output_tokens or content_filter:
            if response.incomplete_details:
                output += f", incomplete_details={response.incomplete_details}"
            raise ResponseError(f"Failed to parse response from OpenAI:\n{output}")

        expcat_resp = response.output_parsed

        # Confirm not None in case value is 0 or "Falsey":
        if response.usage is not None:
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
        Calculate model cost based on token counts.  Model and date specific:

        non_cached_input = input_tokens - cached_tokens
        estimated_cost = (
            non_cached_input * input_rate/1M +
            cached_tokens * cached_input_rate/1M +
            output_tokens * output_rate/1M + tool_costs
        )
        """
        if self.model != "gpt-4o-mini":
            raise NotImplementedError(
                f"Cost calculation only implemented for gpt-4o-mini model, not {self.model}."
            )
        non_cached_input = prompt_tokens - cached_prompt_tokens
        return (
            non_cached_input * INPUT_RATE
            + cached_prompt_tokens * CACHED_INPUT_RATE
            + completion_tokens * OUTPUT_RATE
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
