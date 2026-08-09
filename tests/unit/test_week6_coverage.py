from expenses_ai_agent.api.deps import get_expense_repo, get_user_id
from expenses_ai_agent.api.main import app
from expenses_ai_agent.api.schemas.expense import (
    ExpenseClassifyRequest,
    ExpenseResponse,
)
from expenses_ai_agent.llms.base import MESSAGES, Assistant, LLMProvider
from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.services.classification import (
    ClassificationResult,
    ClassificationService,
)
from expenses_ai_agent.services.preprocessing import (
    InputPreprocessor,
    PreprocessingResult,
)
from expenses_ai_agent.storage.models import (
    Currency,
    Expense,
    ExpenseCategory,
    UserPreference,
)
from expenses_ai_agent.storage.repo import (
    DBExpenseRepo,
    ExpenseRepository,
    InMemoryExpenseRepository,
)

# from expenses_ai_agent.telegram.bot import ExpenseTelegramBot
from expenses_ai_agent.telegram.handlers import (
    CurrencyHandler,
    ExpenseConversationHandler,
)
from expenses_ai_agent.telegram.keyboards import (
    build_category_confirmation_keyboard,
    build_currency_selection_keyboard,
)


class TestImportability:
    """Verify all major components are importable (ensures they exist)."""

    def test_storage_models_importable(self):
        assert Currency is not None
        assert Expense is not None
        assert ExpenseCategory is not None
        assert UserPreference is not None

    def test_storage_repos_importable(self):
        assert ExpenseRepository is not None
        assert InMemoryExpenseRepository is not None
        assert DBExpenseRepo is not None

    def test_llm_components_importable(self):
        assert Assistant is not None
        assert LLMProvider is not None
        assert MESSAGES is not None
        assert OpenAIAssistant is not None
        assert ExpenseCategorizationResponse is not None

    def test_services_importable(self):
        assert ClassificationService is not None
        assert ClassificationResult is not None
        assert InputPreprocessor is not None
        assert PreprocessingResult is not None

    def test_api_components_importable(self):
        assert app is not None
        assert get_expense_repo is not None
        assert get_user_id is not None
        assert ExpenseClassifyRequest is not None
        assert ExpenseResponse is not None

    def test_telegram_components_importable(self):
        #        assert ExpenseTelegramBot is not None
        assert ExpenseConversationHandler is not None
        assert CurrencyHandler is not None
        assert build_category_confirmation_keyboard is not None
        assert build_currency_selection_keyboard is not None
