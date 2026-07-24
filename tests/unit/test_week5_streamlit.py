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
        """Client should have method to classify expense."""
        client = ExpenseAPIClient(base_url="http://test")
        assert hasattr(client, "classify_expense") or hasattr(client, "classify")

    def test_api_client_delete_expense(self):
        """Client should have method to delete an expense."""
        client = ExpenseAPIClient(base_url="http://test")
        assert hasattr(client, "delete_expense")

    def test_api_client_get_summary(self):
        """Client should have method to get analytics summary."""
        client = ExpenseAPIClient(base_url="http://test")
        assert hasattr(client, "get_summary") or hasattr(client, "get_analytics")
