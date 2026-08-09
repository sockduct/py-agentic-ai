from unittest.mock import MagicMock, patch

import pytest
from httpx import RequestError

from expenses_ai_agent.streamlit import app
from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


class TestStreamlitAPIClient:
    """Tests for the Streamlit API client."""

    def test_api_client_exists(self):
        """ExpenseAPIClient should be importable."""
        assert ExpenseAPIClient is not None

    def test_api_client_has_base_url(self):
        """Client should accept base URL configuration."""
        client = ExpenseAPIClient(base_url="http://localhost:8000/api/v1")
        assert client.base_url.rstrip("/") == "http://localhost:8000/api/v1"

    def test_api_client_get_expenses(self):
        """Client should have method to get expenses."""
        client = ExpenseAPIClient(base_url="http://test")
        assert hasattr(client, "get_expenses") or hasattr(client, "list_expenses")

    def test_api_client_classify_expense(self):
        client = ExpenseAPIClient(base_url="http://test")
        response = MagicMock()
        response.json.return_value = {"category": "Food"}

        with patch(
            "expenses_ai_agent.streamlit.api_client.httpx.post",
            return_value=response,
        ) as post:
            result = client.classify_expense("Coffee $5.50", user_id=12345)

        assert result == {"category": "Food"}
        post.assert_called_once_with(
            "http://test/expenses/classify",
            headers={"X-User-ID": "12345"},
            json={"description": "Coffee $5.50"},
        )
        response.raise_for_status.assert_called_once_with()

    def test_api_client_delete_expense(self):
        client = ExpenseAPIClient(base_url="http://test")
        response = MagicMock()

        with patch(
            "expenses_ai_agent.streamlit.api_client.httpx.delete",
            return_value=response,
        ) as delete:
            client.delete_expense(7)

        delete.assert_called_once_with("http://test/expenses/7")
        response.raise_for_status.assert_called_once_with()

    def test_api_client_get_summary(self):
        """Client should have method to get analytics summary."""
        client = ExpenseAPIClient(base_url="http://test")
        assert hasattr(client, "get_summary") or hasattr(client, "get_analytics")

    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [(200, True), (503, False)],
    )
    def test_api_client_health_check(self, status_code, expected):
        client = ExpenseAPIClient(base_url="http://test")
        response = MagicMock(status_code=status_code)

        with patch(
            "expenses_ai_agent.streamlit.api_client.httpx.get",
            return_value=response,
        ) as get:
            result = client.health_check()

        assert result is expected
        get.assert_called_once_with("http://test/health", timeout=5.0)

    def test_api_client_health_check_handles_request_error(self):
        client = ExpenseAPIClient(base_url="http://test")

        with patch(
            "expenses_ai_agent.streamlit.api_client.httpx.get",
            side_effect=RequestError("connection refused"),
        ):
            result = client.health_check()

        assert result is False


class TestStreamlitApp:
    """Tests for the main Streamlit app."""

    def test_app_module_exists(self):
        """Main app module should be importable."""
        assert app is not None
