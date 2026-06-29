from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import create_autospec, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from typer.testing import CliRunner

from expenses_ai_agent.cli.cli import app
from expenses_ai_agent.llms.base import Assistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.prompts.system import CLASSIFICATION_PROMPT
from expenses_ai_agent.prompts.user import USER_PROMPT
from expenses_ai_agent.services.classification import (
    ClassificationResult,
    ClassificationService,
)
from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.models import Currency, Expense, ExpenseCategory
from expenses_ai_agent.storage.repo import DBExpenseRepo, ExpenseRepository


class TestClassificationPrompt:
    """Tests for the system prompt."""

    def test_classification_prompt_exists(self):
        """CLASSIFICATION_PROMPT should be defined as a string constant."""
        assert isinstance(CLASSIFICATION_PROMPT, str)
        assert len(CLASSIFICATION_PROMPT) > 100

    def test_classification_prompt_contains_categories(self):
        """System prompt should mention all 12 expense categories."""
        required_categories = [
            "Food",
            "Transport",
            "Entertainment",
            "Shopping",
            "Health",
            "Bills",
            "Education",
            "Travel",
            "Services",
            "Gifts",
            "Investments",
            "Other",
        ]

        prompt_lower = CLASSIFICATION_PROMPT.lower()
        for category in required_categories:
            assert category.lower() in prompt_lower, f"Category '{category}' not found"

    def test_classification_prompt_mentions_json_output(self):
        """System prompt should mention JSON output format."""
        assert "json" in CLASSIFICATION_PROMPT.lower()


class TestUserPrompt:
    """Tests for the user prompt template."""

    def test_user_prompt_exists(self):
        """USER_PROMPT should be defined."""
        assert isinstance(USER_PROMPT, str)

    def test_user_prompt_has_placeholder(self):
        """USER_PROMPT should have a placeholder."""
        assert "{" in USER_PROMPT and "}" in USER_PROMPT

    def test_user_prompt_can_be_formatted(self):
        """USER_PROMPT should be formattable."""
        try:
            formatted = USER_PROMPT.format(expense_description="Coffee $5.50")
            assert "Coffee" in formatted or "5.50" in formatted
        except KeyError as e:
            assert "expense" in str(e).lower()


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_classification_result_has_response(self):
        """ClassificationResult should contain the LLM response."""
        response = ExpenseCategorizationResponse(
            category="Food",
            total_amount=Decimal("10.00"),
            currency=Currency.EUR,
            confidence=0.9,
            cost=Decimal("0.001"),
        )

        result = ClassificationResult(response=response, persisted=False)

        assert result.response == response
        assert result.persisted is False

    def test_classification_result_tracks_persistence(self):
        """ClassificationResult should track persistence status."""
        response = ExpenseCategorizationResponse(
            category="Transport",
            total_amount=Decimal("25.00"),
            currency=Currency.USD,
            confidence=0.85,
            cost=Decimal("0.002"),
        )

        result_persisted = ClassificationResult(response=response, persisted=True)
        result_not = ClassificationResult(response=response, persisted=False)

        assert result_persisted.persisted is True
        assert result_not.persisted is False


class TestClassificationService:
    """Tests for ClassificationService."""

    @pytest.fixture
    def mock_assistant(self):
        assistant = create_autospec(Assistant)
        assistant.completion.return_value = ExpenseCategorizationResponse(
            category="Food",
            total_amount=Decimal("5.50"),
            currency=Currency.USD,
            confidence=0.95,
            cost=Decimal("0.001"),
        )
        return assistant

    @pytest.fixture
    def mock_expense_repo(self):
        return create_autospec(ExpenseRepository)

    def test_service_initialization(self, mock_assistant):
        service = ClassificationService(assistant=mock_assistant)
        assert service.assistant == mock_assistant

    def test_classify_calls_assistant(self, mock_assistant):
        service = ClassificationService(assistant=mock_assistant)
        result = service.classify("Coffee at Starbucks $5.50")

        mock_assistant.completion.assert_called_once()
        assert result.response.category == "Food"

    def test_classify_without_persistence(self, mock_assistant):
        service = ClassificationService(assistant=mock_assistant)
        result = service.classify("Test expense", persist=False)

        assert result.persisted is False

    def test_classify_with_persistence(self, mock_assistant, mock_expense_repo):
        service = ClassificationService(
            assistant=mock_assistant,
            expense_repo=mock_expense_repo,
        )

        result = service.classify("Coffee $5.50", persist=True)

        assert result.persisted is True
        mock_expense_repo.add.assert_called_once()

    def test_persist_with_category_override(self, mock_assistant, mock_expense_repo):
        service = ClassificationService(
            assistant=mock_assistant,
            expense_repo=mock_expense_repo,
        )

        response = ExpenseCategorizationResponse(
            category="Food",
            total_amount=Decimal("10.00"),
            currency=Currency.EUR,
            confidence=0.6,
            cost=Decimal("0.001"),
        )

        service.persist_with_category(
            expense_description="Movie snacks",
            category_name="Entertainment",
            response=response,
        )

        mock_expense_repo.add.assert_called_once()

    def test_service_builds_correct_messages(self, mock_assistant):
        service = ClassificationService(assistant=mock_assistant)
        service.classify("Test expense")

        call_args = mock_assistant.completion.call_args
        messages = call_args[0][0]

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


class TestDBExpenseRepo:
    """Tests for DBExpenseRepo."""

    def test_db_expense_repo_add_and_get(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        expense = Expense(
            amount=Decimal("42.50"),
            currency=Currency.EUR,
            description="Lunch",
            category=ExpenseCategory.FOOD,
        )
        repo.add(expense)

        result = repo.get(expense.id)
        assert result is not None
        assert result.amount == Decimal("42.50")

    def test_db_expense_repo_list(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        repo.add(Expense(amount=Decimal("10.00"), currency=Currency.EUR))
        repo.add(Expense(amount=Decimal("20.00"), currency=Currency.USD))

        expenses = repo.get_all()
        assert len(expenses) == 2

    def test_db_expense_repo_delete(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        expense = Expense(amount=Decimal("15.00"), currency=Currency.EUR)
        repo.add(expense)
        expense_id = expense.id

        repo.delete(expense_id)
        assert repo.get(expense_id) is None

    def test_db_expense_repo_delete_nonexistent_raises(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        with pytest.raises(ExpenseNotFoundError):
            repo.delete(99999)

    def test_db_expense_repo_search_by_category(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        repo.add(
            Expense(
                amount=Decimal("10"),
                currency=Currency.EUR,
                category=ExpenseCategory.FOOD,
            )
        )
        repo.add(
            Expense(
                amount=Decimal("20"),
                currency=Currency.EUR,
                category=ExpenseCategory.FOOD,
            )
        )
        repo.add(
            Expense(
                amount=Decimal("30"),
                currency=Currency.EUR,
                category=ExpenseCategory.TRANSPORT,
            )
        )

        food_expenses = repo.search_by_category(ExpenseCategory.FOOD)
        assert len(food_expenses) == 2

    def test_db_expense_repo_search_by_dates(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)

        repo.add(Expense(amount=Decimal("10"), currency=Currency.EUR, date=now))
        repo.add(Expense(amount=Decimal("20"), currency=Currency.EUR, date=yesterday))
        repo.add(Expense(amount=Decimal("30"), currency=Currency.EUR, date=last_week))

        start = now - timedelta(days=3)
        results = repo.search_by_dates(start, now)

        assert len(results) == 2

    def test_db_expense_repo_list_by_user(self, db_session):
        repo = DBExpenseRepo(db_url="sqlite:///:memory:", session=db_session)

        repo.add(
            Expense(amount=Decimal("10"), currency=Currency.EUR, telegram_user_id=100)
        )
        repo.add(
            Expense(amount=Decimal("20"), currency=Currency.EUR, telegram_user_id=100)
        )
        repo.add(
            Expense(amount=Decimal("30"), currency=Currency.EUR, telegram_user_id=200)
        )

        user_100_expenses = repo.list_by_user(telegram_user_id=100)
        assert len(user_100_expenses) == 2


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_classification_response():
    return ExpenseCategorizationResponse(
        category="Food",
        total_amount=Decimal("5.50"),
        currency=Currency.USD,
        confidence=0.95,
        cost=Decimal("0.001"),
        comments="Coffee purchase",
    )


class TestCLIApp:
    """Tests for CLI application."""

    def test_cli_app_exists(self):
        assert app is not None

    def test_classify_command_exists(self, cli_runner):
        result = cli_runner.invoke(app, ["classify", "--help"])
        assert result.exit_code == 0

    def test_classify_requires_description(self, cli_runner):
        result = cli_runner.invoke(app, [])
        assert result.exit_code != 0 or "missing" in result.output.lower()

    def test_classify_with_mocked_service(
        self, cli_runner, mock_classification_response
    ):
        with patch(
            "expenses_ai_agent.cli.cli.ClassificationService"
        ) as mock_service_cls:
            mock_service = create_autospec(ClassificationService)
            mock_result = create_autospec(ClassificationResult)
            mock_result.response = mock_classification_response
            mock_result.persisted = False
            mock_service.classify.return_value = mock_result
            mock_service_cls.return_value = mock_service

            with patch("expenses_ai_agent.cli.cli.OpenAIAssistant"):
                result = cli_runner.invoke(app, ["Coffee at Starbucks $5.50"])
                assert result.exit_code == 0 or "Food" in result.output

    def test_classify_db_option_exists(self, cli_runner):
        result = cli_runner.invoke(app, ["classify", "--help"])
        assert "--db" in result.output or "database" in result.output.lower()

    def test_cli_outputs_category_info(self, cli_runner, mock_classification_response):
        with patch(
            "expenses_ai_agent.cli.cli.ClassificationService"
        ) as mock_service_cls:
            mock_service = create_autospec(ClassificationService)
            mock_result = create_autospec(ClassificationResult)
            mock_result.response = mock_classification_response
            mock_result.persisted = False
            mock_service.classify.return_value = mock_result
            mock_service_cls.return_value = mock_service

            with patch("expenses_ai_agent.cli.cli.OpenAIAssistant"):
                result = cli_runner.invoke(app, ["Test expense"])
                output = result.output
                assert "Food" in output or "5.50" in output or "Category" in output
