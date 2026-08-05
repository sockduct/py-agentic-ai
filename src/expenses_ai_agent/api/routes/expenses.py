from fastapi import APIRouter, Depends, HTTPException, status

from expenses_ai_agent.api.deps import get_expense_repo, get_user_id
from expenses_ai_agent.api.schemas import (
    ExpenseClassifyRequest,
    ExpenseListResponse,
    ExpenseResponse,
)
from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.llms.output import ExpenseCategorizationResponse
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.storage.exceptions import ExpenseNotFoundError
from expenses_ai_agent.storage.repo import ExpenseRepository

router = APIRouter(prefix="/expenses", tags=["Expenses"])
MODEL = "gpt-4o-mini"


"""
Requirements:
All routes receive user_id: int from get_user_id — always scoped to a user, never None.

* GET /expenses/ — returns ExpenseListResponse
    call repo.list_by_user(user_id)
* GET /expenses/{expense_id} — returns ExpenseResponse
    call repo.get(expense_id) (integer only, no user_id)
    wrap in try/except ExpenseNotFoundError and raise HTTP 404 — the repo raises, it does not return None
* DELETE /expenses/{expense_id} — returns 204
    call repo.delete(expense_id) with the integer only (no user_id)
* POST /expenses/classify — construct an Assistant instance (e.g. OpenAIAssistant(...)) and
    pass it as the required first argument:
        ClassificationService(assistant=assistant, expense_repo=repo).classify(request.description)
    it returns a ClassificationResult with a .response attribute (ExpenseCategorizationResponse)
    return result.response directly using response_model=ExpenseCategorizationResponse
    do not call any repo method here
"""


@router.get("/", response_model=ExpenseListResponse)
def list_expenses(
    page: int = 1,
    page_size: int = 20,
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_id: int = Depends(get_user_id),
) -> ExpenseListResponse:
    # Original - all expenses:
    # return expense_repo.get_all()
    # Updated - per user:
    # return expense_repo.list_by_user(user_id)
    expenses = expense_repo.list_by_user(user_id)
    start = (page - 1) * page_size
    end = start + page_size
    return ExpenseListResponse(
        items=[
            ExpenseResponse.model_validate(expense) for expense in expenses[start:end]
        ],
        total=len(expenses),
        page=page,
        page_size=page_size,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense_by_id(
    expense_id: int,
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_id: int = Depends(get_user_id),
) -> ExpenseResponse:
    try:
        expense = expense_repo.get(expense_id)
        if expense and expense.telegram_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ExpenseResponse.model_validate(expense)
    except ExpenseNotFoundError as err:
        raise HTTPException(status_code=404, detail="Expense not found") from err


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_id: int = Depends(get_user_id),
) -> None:
    try:
        if (
            expense := expense_repo.get(expense_id)
        ) and expense.telegram_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
            )
        expense_repo.delete(expense_id)
    except ExpenseNotFoundError as err:
        raise HTTPException(status_code=404, detail="Expense not found") from err


# Not sure I met the required spec with this:
@router.post(
    "/classify",
    response_model=ExpenseCategorizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def classify_expense(
    request: ExpenseClassifyRequest,
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_id: int = Depends(get_user_id),
) -> ExpenseCategorizationResponse:
    assistant: OpenAIAssistant = OpenAIAssistant(model=MODEL)
    service = ClassificationService(assistant=assistant, expense_repo=expense_repo)
    result = service.classify(request.description, persist=True)
    return result.response
