import typer
from decouple import config
from openai import OpenAIError
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.services.classification import (
    ClassificationResult,
    ClassificationService,
)
from expenses_ai_agent.storage.repo import DBExpenseRepo

MODEL = "gpt-4o-mini"
# Persistent storage requires configuring a value in .env:
DB_URL = config("DATABASE_URL", default="sqlite:///:memory:")


app = typer.Typer(
    name="expenses-ai-agent",
    help="AI-powered expense classification",
)
console = Console()


@app.command()
def classify(
    description: str = typer.Argument(..., help="Expense description to classify"),
    db: bool = typer.Option(False, "--db", help="Persist to database"),
):
    """Classify an expense using AI."""
    try:
        service = _build_service(db=db)
        result = service.classify(description, persist=db)

        # Display results
        _display_result(result)
    except (OpenAIError, ValidationError) as err:
        console.print(f"[red]Error: {err}[/red]")
        raise typer.Exit(code=1) from err


def _build_service(
    db: bool, *, model: str = MODEL, db_url: str = DB_URL
) -> ClassificationService:
    assistant = OpenAIAssistant(model=model)
    expense_repo = DBExpenseRepo(db_url=db_url) if db else None
    return ClassificationService(assistant=assistant, expense_repo=expense_repo)


def _display_result(result: ClassificationResult) -> None:
    table = Table(title="Classification Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    response = result.response
    table.add_row("Category", response.category)
    table.add_row("Amount", f"{response.total_amount}")
    table.add_row("Currency", response.currency)
    table.add_row("Confidence", f"{response.confidence:.0%}")
    table.add_row("Persisted", "Yes" if result.persisted else "No")

    console.print(table)
