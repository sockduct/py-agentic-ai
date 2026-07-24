"""
Build streamlit/api_client.py with ExpenseAPIClient:

__init__(self, base_url: str)
get_expenses(user_id: int | None = None) -> list[dict] — GET /expenses/
    * The endpoint wraps results as {"items": [...], "total": n}, so unpack with
      response.json()["items"] before returning
      Note:  Total is not needed by the frontend and can be discarded
classify_expense(description: str, user_id: int | None = None) -> dict
    * POST /expenses/classify
delete_expense(expense_id: int) -> None
    * DELETE /expenses/{expense_id}
get_summary(user_id: int | None = None) -> dict
    * GET /analytics/summary

Use httpx for HTTP requests and call raise_for_status() to propagate errors.
Methods that accept user_id should forward it as an X-User-ID header:
    Pass headers={"X-User-ID": str(user_id)} when user_id is not None
"""


class ExpenseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_expenses(self, user_id: int | None = None) -> list[dict]:
        raise NotImplementedError

    def classify_expense(self, description: str, user_id: int | None = None) -> dict:
        raise NotImplementedError

    def delete_expense(self, expense_id: int) -> None:
        raise NotImplementedError

    def get_summary(self, user_id: int | None = None) -> dict:
        raise NotImplementedError
