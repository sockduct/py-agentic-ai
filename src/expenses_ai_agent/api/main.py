from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from expenses_ai_agent.api.deps import get_db_engine
from expenses_ai_agent.api.routes import analytics, categories, expenses, health, root


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifecycle handler."""
    engine = get_db_engine()
    try:
        # Startup: create database tables
        SQLModel.metadata.create_all(engine)
        yield
    finally:
        # Shutdown: cleanup resources (if needed)
        engine.dispose()


app = FastAPI(
    title="Expense API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router, prefix="")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
