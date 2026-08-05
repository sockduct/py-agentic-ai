import httpx


class ExpenseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _headers(self, user_id: int | None) -> dict[str, str]:
        return {"X-User-ID": str(user_id)} if user_id is not None else {}

    def get_expenses(self, user_id: int | None = None) -> list[dict]:
        response = httpx.get(
            f"{self.base_url}/expenses/", headers=self._headers(user_id)
        )
        response.raise_for_status()
        return response.json()["items"]  # API returns {"items": [...], "total": n}

    def classify_expense(self, description: str, user_id: int | None = None) -> dict:
        response = httpx.post(
            f"{self.base_url}/expenses/classify",
            headers=self._headers(user_id),
            json={"description": description},
        )
        response.raise_for_status()
        return response.json()

    def delete_expense(self, expense_id: int) -> None:
        response = httpx.delete(f"{self.base_url}/expenses/{expense_id}")
        response.raise_for_status()

    def get_summary(self, user_id: int | None = None) -> dict:
        response = httpx.get(
            f"{self.base_url}/analytics/summary", headers=self._headers(user_id)
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except httpx.RequestError:
            return False
