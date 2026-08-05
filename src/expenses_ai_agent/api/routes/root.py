from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Root"])


@router.get("/")
def list_routes() -> dict[str, str]:
    return {
        "analytics": "/api/v1/analytics",
        "categories": "/api/v1/categories",
        "documentation": "/docs",
        "expenses": "/api/v1/expenses",
        "health": "/api/v1/health",
    }
