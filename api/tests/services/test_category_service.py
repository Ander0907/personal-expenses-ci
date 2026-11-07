"""Unit tests for ``app.services.category_service``.

The repository is an autospec mock: no session, no database.
"""

from decimal import Decimal
from unittest.mock import create_autospec

import pytest

from app.core.exceptions import DuplicateCategoryError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate
from app.services.category_service import CategoryService


@pytest.fixture
def repository() -> CategoryRepository:
    """Provide an autospec repository that finds no existing category.

    Returns:
        A mock ``CategoryRepository``.
    """
    mock = create_autospec(CategoryRepository, instance=True)
    mock.get_by_name_case_insensitive.return_value = None
    return mock


def make_data() -> CategoryCreate:
    """Build a valid creation payload.

    Returns:
        A ``CategoryCreate``.
    """
    return CategoryCreate(
        name="Food", monthly_budget=Decimal("150.00"), is_active=False
    )


def test_create_adds_a_category_built_from_the_input(
    repository: CategoryRepository,
) -> None:
    """Create persists a category mirroring the payload and returns it."""
    stored = Category(id=1, name="Food", monthly_budget=Decimal("150.00"))
    repository.add.return_value = stored  # type: ignore[attr-defined]

    result = CategoryService(repository).create(make_data())

    assert result is stored
    repository.add.assert_called_once()  # type: ignore[attr-defined]
    added = repository.add.call_args.args[0]  # type: ignore[attr-defined]
    assert isinstance(added, Category)
    assert added.name == "Food"
    assert added.monthly_budget == Decimal("150.00")
    assert added.is_active is False


def test_create_rejects_a_name_that_exists_in_another_case(
    repository: CategoryRepository,
) -> None:
    """Create raises a duplicate error and never adds when the name exists."""
    repository.get_by_name_case_insensitive.return_value = Category(  # type: ignore[attr-defined]
        id=1, name="Food", monthly_budget=Decimal("1"), is_active=True
    )
    data = CategoryCreate(name="food", monthly_budget=Decimal("1"))

    with pytest.raises(DuplicateCategoryError) as raised:
        CategoryService(repository).create(data)

    assert raised.value.name == "food"
    repository.get_by_name_case_insensitive.assert_called_once_with("food")  # type: ignore[attr-defined]
    repository.add.assert_not_called()  # type: ignore[attr-defined]


def test_list_delegates_to_the_repository(repository: CategoryRepository) -> None:
    """List returns what the repository returns for the same pagination."""
    categories = [Category(id=1, name="A", monthly_budget=Decimal("1"))]
    repository.list.return_value = categories  # type: ignore[attr-defined]

    result = CategoryService(repository).list(limit=10, offset=20)

    assert result is categories
    repository.list.assert_called_once_with(limit=10, offset=20)  # type: ignore[attr-defined]
