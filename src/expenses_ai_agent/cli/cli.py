import typer
from decouple import config

### Need when add try/except back - see below:
### from openai import OpenAIError
### from pydantic import ValidationError
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
):
    """Classify an expense using AI."""
    ### The try/except needs to go in for "production" - however; I keep getting
    ### sporadic errors from OpenAI API calls and this hides the details I need
    ### to fix it.  Once all issues are robustly addressed, I will add it back.
    ### try:
    service = _build_service(db=db)
    with service:
        result = service.classify(description, persist=db)

    # Display results
    _display_result(result, verbose=verbose)
    """
    except (OpenAIError, ValidationError) as err:
        console.print(f"[red]Error: {err}[/red]")
        raise typer.Exit(code=1) from err
    """


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
        if response.comments:
            table.add_row("Cost", f"{response.comments}")
        # Commented out for now as removed this from LLM parsed response:
        # table.add_row("Timestamp", f"{response.timestamp:%Y-%m-%d %H:%M:%S}")
    table.add_row("Persisted", "Yes" if result.persisted else "No")

    console.print(table)
