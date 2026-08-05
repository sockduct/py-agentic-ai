from fastapi import APIRouter

from expenses_ai_agent.storage.models import ExpenseCategory

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/")
def list_categories() -> list[str]:
    """
    GET /categories/ — returns list[str] of all ExpenseCategory enum values
    No schema needed, FastAPI serializes plain Python types directly
    """
    return [str(ec) for ec in ExpenseCategory]
