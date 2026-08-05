from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest
from telegram.ext import ConversationHandler

from expenses_ai_agent.llms.base import Assistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.storage.models import Currency
from expenses_ai_agent.storage.repo import DBUserPreferenceRepo
from expenses_ai_agent.telegram.exceptions import (
    ClassificationError,
    InvalidInputError,
    TelegramBotError,
)
from expenses_ai_agent.telegram.handlers import (
    ConversationState,
    CurrencyHandler,
    ExpenseConversationHandler,
    cancel_command,
    help_command,
    start_command,
)
from expenses_ai_agent.telegram.keyboards import CATEGORY_CALLBACK_PREFIX


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.message = MagicMock()
    update.message.text = "Coffee $5.50"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


@pytest.fixture
def mock_callback_update():
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.callback_query = MagicMock()
    update.callback_query.data = "category:Food"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


def _response() -> ExpenseCategorizationResponse:
    return ExpenseCategorizationResponse(
        category="Food",
        total_amount=Decimal("5.50"),
        currency=Currency.USD,
        confidence=0.95,
        cost=Decimal("0.001"),
    )


class TestExceptions:
    def test_hierarchy(self):
        assert isinstance(InvalidInputError("x"), TelegramBotError)
        assert isinstance(ClassificationError("x"), TelegramBotError)
        assert isinstance(TelegramBotError("x"), Exception)


class TestCommandHandlers:
    async def test_start_replies(self, mock_update, mock_context):
        await start_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

    async def test_help_replies(self, mock_update, mock_context):
        await help_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

    async def test_cancel_returns_end(self, mock_update, mock_context):
        assert (
            await cancel_command(mock_update, mock_context) == ConversationHandler.END
        )

    async def test_cancel_without_message_still_ends(self, mock_context):
        update = MagicMock()
        update.message = None
        assert await cancel_command(update, mock_context) == ConversationHandler.END

    async def test_start_and_help_without_message_are_noops(self, mock_context):
        update = MagicMock()
        update.message = None
        await start_command(update, mock_context)
        await help_command(update, mock_context)


class TestExpenseConversationHandler:
    def _handler(self):
        return ExpenseConversationHandler(
            db_url="sqlite:///:memory:", api_key="test-key"
        )

    def test_build_returns_conversation_handler(self):
        assert isinstance(self._handler().build(), ConversationHandler)

    def test_build_routes_category_taps_with_correct_pattern(self):
        conv = self._handler().build()
        state_handlers = conv.states[ConversationState.WAITING_FOR_CATEGORY]
        assert len(state_handlers) == 1
        assert state_handlers[0].pattern.pattern == f"^{CATEGORY_CALLBACK_PREFIX}"

    async def test_invalid_input_ends_conversation(self, mock_update, mock_context):
        mock_update.message.text = "ab"
        result = await self._handler().handle_expense_text(mock_update, mock_context)
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called()

    async def test_valid_input_classifies_and_shows_keyboard(
        self, mock_update, mock_context
    ):
        handler = self._handler()
        with patch.object(handler, "_build_assistant") as mock_build:
            assistant = create_autospec(Assistant)
            assistant.completion.return_value = _response()
            mock_build.return_value = assistant
            result = await handler.handle_expense_text(mock_update, mock_context)
        assert result == ConversationState.WAITING_FOR_CATEGORY
        assert "expense_description" in mock_context.user_data

    async def test_category_selection_persists(
        self, mock_callback_update, mock_context
    ):
        mock_context.user_data["expense_description"] = "Coffee $5.50"
        mock_context.user_data["classification_response"] = _response()
        handler = self._handler()
        with patch.object(handler, "_build_service") as mock_build:
            mock_build.return_value = MagicMock()
            result = await handler.handle_category_selection(
                mock_callback_update, mock_context
            )
        assert result == ConversationHandler.END
        mock_callback_update.callback_query.answer.assert_awaited()

    async def test_telegram_user_id_forwarded(self, mock_callback_update, mock_context):
        mock_context.user_data["expense_description"] = "Coffee $5.50"
        mock_context.user_data["classification_response"] = _response()
        handler = self._handler()
        with patch.object(handler, "_build_service") as mock_build:
            service = MagicMock()
            mock_build.return_value = service
            await handler.handle_category_selection(mock_callback_update, mock_context)
        kwargs = service.persist_with_category.call_args.kwargs
        assert kwargs.get("telegram_user_id") == 12345

    async def test_warning_input_still_classifies(self, mock_update, mock_context):
        mock_update.message.text = "Lunch at cafe"  # no amount -> warning, not error
        handler = self._handler()
        with patch.object(handler, "_build_assistant") as mock_build:
            assistant = create_autospec(Assistant)
            assistant.completion.return_value = _response()
            mock_build.return_value = assistant
            result = await handler.handle_expense_text(mock_update, mock_context)
        assert result == ConversationState.WAITING_FOR_CATEGORY
        assert (
            mock_update.message.reply_text.call_count >= 2
        )  # warning note + classification

    async def test_classification_failure_replies_and_ends(
        self, mock_update, mock_context
    ):
        handler = self._handler()
        service = MagicMock()
        service.classify.side_effect = RuntimeError("service unavailable")

        with patch.object(handler, "_build_service", return_value=service):
            result = await handler.handle_expense_text(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_awaited_once_with(
            "Sorry, I couldn't classify that. Please try again in a moment."
        )

    async def test_category_selection_session_expired(
        self, mock_callback_update, mock_context
    ):
        # user_data is empty (bot restarted between message and tap)
        result = await self._handler().handle_category_selection(
            mock_callback_update, mock_context
        )
        assert result == ConversationHandler.END
        mock_callback_update.callback_query.edit_message_text.assert_awaited()

    async def test_missing_message_ends_conversation(self, mock_update, mock_context):
        mock_update.message = None  # e.g. an edited message, not a new one
        result = await self._handler().handle_expense_text(mock_update, mock_context)
        assert result == ConversationHandler.END

    async def test_missing_callback_query_ends_conversation(
        self, mock_callback_update, mock_context
    ):
        mock_callback_update.callback_query = None
        result = await self._handler().handle_category_selection(
            mock_callback_update, mock_context
        )
        assert result == ConversationHandler.END


class TestCurrencyHandler:
    async def test_currency_command_shows_keyboard(self, mock_update, mock_context):
        await CurrencyHandler(db_url="sqlite:///:memory:").currency_command(
            mock_update, mock_context
        )
        assert "reply_markup" in mock_update.message.reply_text.call_args.kwargs

    async def test_handle_currency_selection(self, mock_callback_update, mock_context):
        mock_callback_update.callback_query.data = "setcurrency:EUR"
        handler = CurrencyHandler(db_url="sqlite:///:memory:")
        with patch("expenses_ai_agent.telegram.handlers.DBUserPreferenceRepo"):
            await handler.handle_currency_selection(mock_callback_update, mock_context)
        mock_callback_update.callback_query.answer.assert_awaited()

    async def test_currency_command_without_message_is_noop(self, mock_context):
        update = MagicMock()
        update.message = None
        await CurrencyHandler(db_url="sqlite:///:memory:").currency_command(
            update, mock_context
        )

    async def test_currency_selection_without_query_is_noop(self, mock_context):
        update = MagicMock()
        update.callback_query = None
        with patch("expenses_ai_agent.telegram.handlers.DBUserPreferenceRepo") as repo:
            await CurrencyHandler(
                db_url="sqlite:///:memory:"
            ).handle_currency_selection(update, mock_context)
        repo.assert_not_called()


class TestDBUserPreferenceRepoIntegration:
    def test_upsert_inserts_then_updates(self):
        with DBUserPreferenceRepo(db_url="sqlite:///:memory:") as repo:
            repo.upsert(telegram_user_id=42, currency=Currency.USD)
            assert repo.get_by_user_id(42).preferred_currency == Currency.USD
            repo.upsert(telegram_user_id=42, currency=Currency.EUR)
            assert repo.get_by_user_id(42).preferred_currency == Currency.EUR

    def test_get_unknown_user_returns_none(self):
        with DBUserPreferenceRepo(db_url="sqlite:///:memory:") as repo:
            assert repo.get_by_user_id(99999) is None

    def test_context_manager_closes_owned_resources(self):
        engine = MagicMock()
        session = MagicMock()

        with (
            patch("expenses_ai_agent.storage.repo.create_engine", return_value=engine),
            patch("expenses_ai_agent.storage.repo.SQLModel.metadata.create_all"),
            patch("expenses_ai_agent.storage.repo.Session", return_value=session),
        ):
            with DBUserPreferenceRepo(db_url="sqlite:///:memory:") as repo:
                assert repo.db is session

        session.close.assert_called_once_with()
        engine.dispose.assert_called_once_with()
