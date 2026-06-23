import inspect
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol  # used in test_assistant_protocol_exists assertion below
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from expenses_ai_agent.llms.base import COST, MESSAGES, Assistant, LLMProvider
from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.storage.models import Currency
from expenses_ai_agent.tools.tools import (
    CURRENCY_CONVERSION_TOOL,
    DATETIME_FORMATTER_TOOL,
)
from expenses_ai_agent.utils.currency import convert_currency
from expenses_ai_agent.utils.date_formatter import format_datetime


class TestExpenseCategorizationResponse:
    """Tests for the structured output model."""

    def test_response_has_required_fields(self):
        """Response model must have all required fields."""
        response = ExpenseCategorizationResponse(
            category="Food",
            total_amount=Decimal("42.50"),
            currency=Currency.EUR,
            confidence=0.95,
            cost=Decimal("0.001"),
        )

        assert response.category == "Food"
        assert response.total_amount == Decimal("42.50")
        assert response.currency == Currency.EUR
        assert response.confidence == 0.95
        assert response.cost == Decimal("0.001")

    def test_response_optional_fields(self):
        """Response should support optional comments."""
        response = ExpenseCategorizationResponse(
            category="Transport",
            total_amount=Decimal("15.00"),
            currency=Currency.USD,
            confidence=0.8,
            cost=Decimal("0.002"),
            comments="Taxi ride to airport",
        )

        assert response.comments == "Taxi ride to airport"

    def test_response_has_timestamp(self):
        """Response should include a timestamp."""
        response = ExpenseCategorizationResponse(
            category="Entertainment",
            total_amount=Decimal("10.00"),
            currency=Currency.EUR,
            confidence=0.9,
            cost=Decimal("0.001"),
        )

        assert hasattr(response, "timestamp")
        assert isinstance(response.timestamp, datetime)

    def test_response_is_pydantic_model(self):
        """Response should be a Pydantic BaseModel for validation."""
        assert issubclass(ExpenseCategorizationResponse, BaseModel)

    def test_response_json_serialization(self):
        """Response should serialize to JSON."""
        response = ExpenseCategorizationResponse(
            category="Food",
            total_amount=Decimal("25.00"),
            currency=Currency.GBP,
            confidence=0.85,
            cost=Decimal("0.001"),
        )

        json_str = response.model_dump_json()
        assert "Food" in json_str
        assert "25" in json_str


class TestAssistantProtocol:
    """Tests for the Assistant Protocol definition."""

    def test_assistant_protocol_exists(self):
        """Assistant should be defined as a Protocol."""
        assert hasattr(Assistant, "__protocol_attrs__") or issubclass(
            Assistant, Protocol
        )

    def test_assistant_has_completion_method(self):
        """Assistant Protocol must define completion method."""
        assert hasattr(Assistant, "completion")

    def test_assistant_has_calculate_cost_method(self):
        """Assistant Protocol must define calculate_cost method."""
        assert hasattr(Assistant, "calculate_cost")

    def test_assistant_has_get_available_models_method(self):
        """Assistant Protocol must define get_available_models method."""
        assert hasattr(Assistant, "get_available_models")

    def test_completion_signature(self):
        """completion should take messages only — no model parameter."""
        params = list(inspect.signature(Assistant.completion).parameters.keys())
        assert "messages" in params
        assert "model" not in params

    def test_completion_return_annotation(self):
        """completion should return ExpenseCategorizationResponse."""
        sig = inspect.signature(Assistant.completion)
        assert sig.return_annotation is ExpenseCategorizationResponse

    def test_calculate_cost_signature(self):
        """calculate_cost should take prompt_tokens and completion_tokens."""
        params = list(inspect.signature(Assistant.calculate_cost).parameters.keys())
        assert "prompt_tokens" in params
        assert "completion_tokens" in params


class TestLLMProvider:
    """Tests for the LLMProvider enumeration."""

    def test_llm_provider_has_openai(self):
        """LLMProvider should include OPENAI."""
        assert hasattr(LLMProvider, "OPENAI")

    def test_llm_provider_has_groq(self):
        """LLMProvider should include GROQ."""
        assert hasattr(LLMProvider, "GROQ")

    def test_llm_provider_is_str_enum(self):
        """LLMProvider should be a StrEnum for string compatibility."""
        assert issubclass(LLMProvider, StrEnum)


class TestTypeAliases:
    """Tests for type alias definitions."""

    def test_messages_type_alias_exists(self):
        """MESSAGES type alias should be defined."""
        sample_messages: MESSAGES = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
        assert len(sample_messages) == 2

    def test_cost_type_alias_exists(self):
        """COST type alias should be defined."""
        sample_cost: COST = {
            "prompt": [Decimal("0.001"), Decimal("0.002")],
            "completion": [Decimal("0.003")],
        }
        assert "prompt" in sample_cost


class TestCurrencyConversion:
    """Tests for the currency conversion utility."""

    def test_convert_currency_function_exists(self):
        """convert_currency function should exist."""
        assert callable(convert_currency)

    def test_convert_currency_returns_decimal(self):
        """Currency conversion should return a Decimal value."""
        with (
            patch("expenses_ai_agent.utils.currency.EXCHANGE_RATE_API_KEY", "test-key"),
            patch("expenses_ai_agent.utils.currency.requests.get") as mock_get,
        ):
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": "success",
                "conversion_rate": 1.1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = convert_currency(Decimal("100"), "EUR", "USD")

            assert isinstance(result, Decimal)

    def test_convert_currency_same_currency(self):
        """Converting to the same currency should return the original amount."""
        result = convert_currency(Decimal("50.00"), "EUR", "EUR")

        assert result == Decimal("50.00")

    def test_convert_currency_applies_rate(self):
        """Conversion should apply the exchange rate correctly."""
        with (
            patch("expenses_ai_agent.utils.currency.EXCHANGE_RATE_API_KEY", "test-key"),
            patch("expenses_ai_agent.utils.currency.requests.get") as mock_get,
        ):
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": "success",
                "conversion_rate": 1.5,
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = convert_currency(Decimal("100"), "EUR", "USD")

            assert result == Decimal("150")


class TestDateFormatter:
    """Tests for the date formatting utility."""

    def test_format_datetime_function_exists(self):
        """format_datetime function should exist."""
        assert callable(format_datetime)

    def test_format_datetime_returns_string(self):
        """Date formatting should return a string."""
        result = format_datetime("2024-06-15T14:30:00+00:00")

        assert isinstance(result, str)

    def test_format_datetime_includes_date_components(self):
        """Formatted datetime should include readable date components."""
        result = format_datetime("2024-06-15T14:30:00+00:00")

        assert "2024" in result or "24" in result
        assert "Jun" in result or "06" in result or "6" in result

    def test_format_datetime_with_timezone(self):
        """Should support timezone conversion."""
        result = format_datetime(
            "2024-06-15T12:00:00+00:00", timezone_str="Europe/Madrid"
        )

        assert isinstance(result, str)


class TestToolSchemas:
    """Tests for OpenAI-compatible tool schemas."""

    def _parent_has_attr(self, parent: object, *args):
        for arg in args:
            assert arg in parent

    def test_currency_tool_schema_exists(self):
        """Currency conversion tool schema should be defined."""
        assert isinstance(CURRENCY_CONVERSION_TOOL, dict)

    def test_currency_tool_has_function_type(self):
        """Tool schema should have type: function."""
        assert CURRENCY_CONVERSION_TOOL.get("type") == "function"

    def test_currency_tool_has_required_structure(self):
        """Tool schema should follow OpenAI function calling format."""

        """
        # Old function format:
        assert "function" in CURRENCY_CONVERSION_TOOL
        func = CURRENCY_CONVERSION_TOOL["function"]

        assert "name" in func
        assert "description" in func
        assert "parameters" in func

        params = func["parameters"]
        assert "type" in params
        assert "properties" in params
        """

        # New function format:
        self._parent_has_attr(
            CURRENCY_CONVERSION_TOOL, "name", "description", "parameters"
        )
        self._parent_has_attr(
            CURRENCY_CONVERSION_TOOL["parameters"], "type", "properties", "required"
        )

    def test_datetime_tool_schema_exists(self):
        """Datetime formatter tool schema should be defined."""
        assert isinstance(DATETIME_FORMATTER_TOOL, dict)
        assert DATETIME_FORMATTER_TOOL.get("type") == "function"

    def test_datetime_tool_has_function_type(self):
        """Tool schema should have type: function."""
        assert DATETIME_FORMATTER_TOOL.get("type") == "function"

    def test_datetime_tool_has_required_structure(self):
        """Tool schema should follow OpenAI function calling format."""

        self._parent_has_attr(
            DATETIME_FORMATTER_TOOL, "name", "description", "parameters"
        )
        self._parent_has_attr(
            DATETIME_FORMATTER_TOOL["parameters"], "type", "properties", "required"
        )


class TestOpenAIAssistant:
    """Tests for OpenAIAssistant implementation."""

    def test_openai_assistant_exists(self):
        """OpenAIAssistant should be importable."""
        assert OpenAIAssistant is not None

    def test_openai_assistant_satisfies_protocol(self):
        """OpenAIAssistant should satisfy the Assistant Protocol."""
        assert hasattr(OpenAIAssistant, "completion")
        assert hasattr(OpenAIAssistant, "calculate_cost")
        assert hasattr(OpenAIAssistant, "get_available_models")

    def test_calculate_cost_returns_decimal(self):
        """calculate_cost should return a Decimal."""
        with patch("expenses_ai_agent.llms.openai.OpenAI"):
            assistant = OpenAIAssistant(model="gpt-4o-mini", api_key="test-key")
            cost = assistant.calculate_cost(100, 50)
            assert isinstance(cost, Decimal)

    def test_completion_calls_openai_and_returns_response(self):
        """completion should call the OpenAI API and return ExpenseCategorizationResponse."""
        # MagicMock is used here (not create_autospec) because the OpenAI SDK's
        # deeply-nested attributes don't autospec cleanly. Week 3 uses
        # create_autospec(Assistant) where we control the interface.
        with patch("expenses_ai_agent.llms.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client

            mock_parsed = ExpenseCategorizationResponse(
                category="Food",
                total_amount=Decimal("5.50"),
                currency=Currency.USD,
                confidence=0.95,
                cost=Decimal("0.001"),
            )
            mock_response = MagicMock()
            """
            # Old API:
            mock_response.choices[0].message.parsed = mock_parsed
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_client.beta.chat.completions.parse.return_value = mock_response
            """
            # Replacement responses API:
            mock_response.output_parsed = mock_parsed
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_client.responses.parse.return_value = mock_response

            assistant = OpenAIAssistant(model="gpt-4o-mini", api_key="test-key")
            messages = [{"role": "user", "content": "Coffee $5.50"}]
            result = assistant.completion(messages)

            assert isinstance(result, ExpenseCategorizationResponse)
            # Old API:
            # mock_client.beta.chat.completions.parse.assert_called_once()
            # Replacement responses API:
            mock_client.responses.parse.assert_called_once()
