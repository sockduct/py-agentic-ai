from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Expenses"])


@router.get("/")
def list_analytics(): ...
