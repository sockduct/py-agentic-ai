from fastapi import APIRouter, Depends

from expenses_ai_agent.api.deps import get_expense_repo, get_user_id
from expenses_ai_agent.storage.repo import ExpenseRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=dict[str, dict[str, str]])
def list_analytics(
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_id: int = Depends(get_user_id),
) -> dict[str, dict[str, str]]:
    """
    GET /analytics/summary — inject user_id: int = Depends(get_user_id)
    Call repo.get_category_totals(user_id) and repo.get_monthly_totals(user_id)
    Return {"category_totals": {...}, "monthly_totals": {...}} with Decimal
    values serialized as strings
    Use response_model=dict[str, dict[str, str]]
    """
    category_totals = expense_repo.get_category_totals(user_id)
    category_totals_str = {key: str(val) for key, val in category_totals.items()}
    monthly_totals = expense_repo.get_monthly_totals(user_id)
    monthly_totals_str = {key: str(val) for key, val in monthly_totals.items()}

    return {
        "category_totals": category_totals_str,
        "monthly_totals": monthly_totals_str,
    }
