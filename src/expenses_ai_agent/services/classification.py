from dataclasses import dataclass
from types import TracebackType

from expenses_ai_agent.llms.base import MESSAGES, Assistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.prompts.system import CLASSIFICATION_PROMPT
from expenses_ai_agent.prompts.user import USER_PROMPT
from expenses_ai_agent.services.exceptions import MissingRepositoryError
from expenses_ai_agent.storage.models import Expense, ExpenseCategory
from expenses_ai_agent.storage.repo import ExpenseRepository


@dataclass(frozen=True)
class ClassificationResult:
    response: ExpenseCategorizationResponse
    persisted: bool


@dataclass
class ClassificationService:
    assistant: Assistant
    expense_repo: ExpenseRepository | None = None

    def __enter__(self) -> "ClassificationService":
        return self

    def __exit__(
        self, exc_type: type[Exception], exc_value: Exception, tb: TracebackType
    ):
        if hasattr(self.expense_repo, "close"):
            self.expense_repo.close()

    def classify(
        self,
        expense_description: str,
        persist: bool = False,
    ) -> ClassificationResult:
        messages = self._build_messages(expense_description)
        response = self.assistant.completion(messages)

        if persist:
            if self.expense_repo is None:
                raise MissingRepositoryError(
                    f"Unable to persist expense: {expense_description}, no repository provided."
                )
            self._persist_expense(expense_description, response)

        return ClassificationResult(response=response, persisted=persist)

    def persist_with_category(
        self,
        expense_description: str,
        category_name: ExpenseCategory,
        response: ExpenseCategorizationResponse,
        telegram_user_id: int | None = None,
    ) -> None:
        updated_response = ExpenseCategorizationResponse(
            category=category_name,
            total_amount=response.total_amount,
            currency=response.currency,
            confidence=response.confidence,
            cost=response.cost,
        )
        self._persist_expense(expense_description, updated_response, telegram_user_id)

    def _build_messages(self, expense_description: str) -> MESSAGES:
        return [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT.format(expense_description=expense_description),
            },
        ]

    def _persist_expense(
        self,
        expense_description: str,
        response: ExpenseCategorizationResponse,
        telegram_user_id: int | None = None,
    ) -> None:
        expense = Expense(
            amount=response.total_amount,
            currency=response.currency,
            category=response.category,
            description=expense_description,
            telegram_user_id=telegram_user_id,
        )
        if self.expense_repo is None:
            raise MissingRepositoryError(
                f"Unable to persist expense: {expense}, no repository provided."
            )
        self.expense_repo.add(expense)
