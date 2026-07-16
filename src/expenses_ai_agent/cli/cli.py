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
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks"),
):
    """Classify an expense using AI."""
    try:
        service = _build_service(db=db)
        with service:
            result = service.classify(description, persist=db)

        _display_result(result, verbose=verbose)
    except (OpenAIError, ValidationError) as err:
        if debug:
            console.print_exception()
        else:
            console.print(f"[red]Error:[/red] {err}")
            console.print("[dim]Run with --debug for full traceback[/dim]")
        raise typer.Exit(code=1) from err


def _build_service(
    db: bool, *, model: str = MODEL, db_url: str = DB_URL
) -> ClassificationService:
    assistant = OpenAIAssistant(model=model)
    expense_repo = DBExpenseRepo(db_url) if db else None
    return ClassificationService(assistant=assistant, expense_repo=expense_repo)


def _display_result(result: ClassificationResult, *, verbose: bool = False) -> None:
    table = Table(title="Classification Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    response = result.response
    table.add_row("Category", response.category)
    table.add_row("Amount", f"{response.total_amount}")
    table.add_row("Currency", response.currency)
    table.add_row("Confidence", f"{response.confidence:.0%}")
    if verbose:
        table.add_row("Cost", f"{response.cost}")
        if response.comments:
            table.add_row("Comments", f"{response.comments}")
        # Commented out for now as removed this from LLM parsed response:
        # table.add_row("Timestamp", f"{response.timestamp:%Y-%m-%d %H:%M:%S}")
    table.add_row("Persisted", "Yes" if result.persisted else "No")

    console.print(table)
