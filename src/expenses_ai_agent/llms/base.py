from decimal import Decimal
from enum import UNIQUE, StrEnum, auto, verify
from typing import Protocol, Sequence, runtime_checkable

from expenses_ai_agent.llms.output import ExpenseCategorizationResponse

type MESSAGES = list[dict[str, str]]  # Chat message lists
type COST = dict[str, list[Decimal]]  # Cost tracking


@verify(UNIQUE)
class LLMProvider(StrEnum):
    """Abstract model provider"""

    OPENAI = auto()
    GROQ = auto()


@runtime_checkable
class Assistant(Protocol):
    """Abstract model/LLM interactions"""

    def completion(self, messages: MESSAGES) -> ExpenseCategorizationResponse: ...
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> Decimal: ...
    def get_available_models(self) -> Sequence[str]: ...
