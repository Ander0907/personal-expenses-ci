"""Category router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.limits import DEFAULT_LIMIT, MAX_LIMIT, MAX_OFFSET
from app.dependencies import get_category_service
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "The category name already exists."}
    },
)
def create_category(data: CategoryCreate, service: CategoryServiceDep) -> CategoryRead:
    """Create a category.

    Args:
        data: Validated creation payload.
        service: Category service.

    Returns:
        The created category.
    """
    return CategoryRead.model_validate(service.create(data))


@router.get("", response_model=list[CategoryRead])
def list_categories(
    service: CategoryServiceDep,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0, le=MAX_OFFSET)] = 0,
) -> list[CategoryRead]:
    """List categories ordered by name.

    Args:
        service: Category service.
        limit: Maximum number of items (1-500).
        offset: Number of items to skip (0 to ``MAX_OFFSET``).

    Returns:
        The requested page of categories.
    """
    return [
        CategoryRead.model_validate(item)
        for item in service.list(limit=limit, offset=offset)
    ]
