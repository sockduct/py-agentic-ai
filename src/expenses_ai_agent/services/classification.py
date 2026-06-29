from dataclasses import dataclass

from expenses_ai_agent.llms.base import MESSAGES, Assistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.prompts.system import CLASSIFICATION_PROMPT
from expenses_ai_agent.prompts.user import USER_PROMPT
from expenses_ai_agent.services.exceptions import MissingRepositoryError
from expenses_ai_agent.storage.exceptions import InvalidExpenseCategory
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

    def classify(
        self,
        expense_description: str,
        persist: bool = False,
    ) -> ClassificationResult:
        messages = self._build_messages(expense_description)
        response = self.assistant.completion(messages)

        if persist and self.expense_repo:
            self._persist_expense(expense_description, response)

        return ClassificationResult(response=response, persisted=persist)

    def persist_with_category(
        self,
        expense_description: str,
        category_name: str,
        response: ExpenseCategorizationResponse,
    ) -> None:
        # For human-in-the-loop: user corrects the classification
        if category_name.lower() not in [e.value.lower() for e in ExpenseCategory]:
            raise InvalidExpenseCategory(
                f"{category_name} not a valid expense category."
            )
        response.category = ExpenseCategory(category_name.capitalize())
        self._persist_expense(expense_description, response)

    def _build_messages(self, expense_description: str) -> MESSAGES:
        return [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT.format(expense_description=expense_description),
            },
        ]

    def _persist_expense(
        self, expense_description: str, response: ExpenseCategorizationResponse
    ) -> None:
        expense = Expense(
            amount=response.total_amount,
            currency=response.currency,
            category=ExpenseCategory(response.category),
            description=expense_description,
        )
        if self.expense_repo is None:
            raise MissingRepositoryError(
                f"Unable to persist expense: {expense}, no repository provided."
            )
        self.expense_repo.add(expense)
