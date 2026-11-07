"""Expense router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.limits import DEFAULT_LIMIT, MAX_DB_INT, MAX_LIMIT, MAX_OFFSET
from app.dependencies import get_expense_service
from app.schemas.expense import ExpenseCreate, ExpenseCreated, ExpenseRead
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])

ExpenseServiceDep = Annotated[ExpenseService, Depends(get_expense_service)]


@router.post(
    "",
    response_model=ExpenseCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "The category does not exist."},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid payload, future date or inactive category."
        },
    },
)
def create_expense(data: ExpenseCreate, service: ExpenseServiceDep) -> ExpenseCreated:
    """Create an expense.

    Args:
        data: Validated creation payload.
        service: Expense service.

    Returns:
        The created expense with the ``over_budget`` flag.
    """
    created = service.create(data)
    return ExpenseCreated(
        **ExpenseRead.model_validate(created.expense).model_dump(),
        over_budget=created.over_budget,
    )


@router.get(
    "",
    response_model=list[ExpenseRead],
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid filters or unsupported month (InvalidMonthError)."
        }
    },
)
def list_expenses(
    service: ExpenseServiceDep,
    category_id: Annotated[int | None, Query(ge=1, le=MAX_DB_INT)] = None,
    month: Annotated[str | None, Query(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0, le=MAX_OFFSET)] = 0,
) -> list[ExpenseRead]:
    """List expenses, newest first.

    Args:
        service: Expense service.
        category_id: Optional category filter.
        month: Optional ``YYYY-MM`` month filter.
        limit: Maximum number of items (1-500).
        offset: Number of items to skip (0 to ``MAX_OFFSET``).

    Returns:
        The requested page of expenses.
    """
    return [
        ExpenseRead.model_validate(item)
        for item in service.list(
            category_id=category_id, month=month, limit=limit, offset=offset
        )
    ]


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "The expense does not exist."}
    },
)
def delete_expense(
    expense_id: Annotated[int, Path(ge=1, le=MAX_DB_INT)], service: ExpenseServiceDep
) -> None:
    """Delete an expense.

    Args:
        expense_id: Id of the expense to remove.
        service: Expense service.
    """
    service.delete(expense_id)
