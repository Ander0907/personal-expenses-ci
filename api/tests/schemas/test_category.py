"""Unit tests for ``app.schemas.category``.

Validation limits mirror the database column sizes so that bad input becomes a
422 instead of a database error.
"""

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead


def test_category_create_accepts_a_valid_payload() -> None:
    """Category create keeps valid values as given."""
    data = CategoryCreate(
        name="Food", monthly_budget=Decimal("150.00"), is_active=False
    )

    assert data.name == "Food"
    assert data.monthly_budget == Decimal("150.00")
    assert data.is_active is False


def test_category_create_defaults_is_active_to_true() -> None:
    """Category create marks the category active when not told otherwise."""
    data = CategoryCreate(name="Food", monthly_budget=Decimal("1"))

    assert data.is_active is True


def test_category_create_strips_surrounding_whitespace_from_name() -> None:
    """Category create strips whitespace around the name."""
    data = CategoryCreate(name="  Food  ", monthly_budget=Decimal("1"))

    assert data.name == "Food"


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_category_create_rejects_blank_name(name: str) -> None:
    """Category create rejects empty or whitespace-only names."""
    with pytest.raises(ValidationError):
        CategoryCreate(name=name, monthly_budget=Decimal("1"))


@pytest.mark.parametrize("name", ["a\x00b", "a\x07b", "line\nbreak", "tab\there"])
def test_category_create_rejects_control_characters_in_name(name: str) -> None:
    """Category create rejects names containing control characters."""
    with pytest.raises(ValidationError):
        CategoryCreate(name=name, monthly_budget=Decimal("1"))


@pytest.mark.parametrize("name", ["Café ☕", "Ünïcödé"])
def test_category_create_accepts_unicode_names(name: str) -> None:
    """Category create keeps printable unicode names untouched."""
    data = CategoryCreate(name=name, monthly_budget=Decimal("1"))

    assert data.name == name


def test_category_create_accepts_a_name_of_100_characters() -> None:
    """Category create accepts the longest allowed name."""
    data = CategoryCreate(name="a" * 100, monthly_budget=Decimal("1"))

    assert len(data.name) == 100


def test_category_create_rejects_a_name_of_101_characters() -> None:
    """Category create rejects names longer than the column."""
    with pytest.raises(ValidationError):
        CategoryCreate(name="a" * 101, monthly_budget=Decimal("1"))


def test_category_create_requires_a_name() -> None:
    """Category create requires a name."""
    with pytest.raises(ValidationError):
        CategoryCreate.model_validate({"monthly_budget": "1"})


def test_category_create_requires_a_monthly_budget() -> None:
    """Category create requires a monthly budget."""
    with pytest.raises(ValidationError):
        CategoryCreate.model_validate({"name": "Food"})


@pytest.mark.parametrize("budget", ["0", "0.00", "9999999999.99", "10.5"])
def test_category_create_accepts_valid_budgets(budget: str) -> None:
    """Category create accepts budgets within precision and range."""
    data = CategoryCreate.model_validate({"name": "Food", "monthly_budget": budget})

    assert data.monthly_budget == Decimal(budget)


@pytest.mark.parametrize(
    "budget",
    ["-1", "-0.01", "10.123", "10000000000.00", "99999999999"],
)
def test_category_create_rejects_invalid_budgets(budget: str) -> None:
    """Category create rejects negative, over-precise or too large budgets."""
    with pytest.raises(ValidationError):
        CategoryCreate.model_validate({"name": "Food", "monthly_budget": budget})


def test_category_create_forbids_extra_fields() -> None:
    """Category create rejects unknown fields such as ``id``."""
    payload: dict[str, Any] = {"id": 1, "name": "Food", "monthly_budget": "1"}

    with pytest.raises(ValidationError):
        CategoryCreate.model_validate(payload)


def test_category_read_is_built_from_an_orm_instance() -> None:
    """Category read reads attributes from a ``Category`` instance."""
    category = Category(
        id=7, name="Food", monthly_budget=Decimal("150.00"), is_active=True
    )

    read = CategoryRead.model_validate(category)

    assert read.id == 7
    assert read.name == "Food"
    assert read.monthly_budget == Decimal("150.00")
    assert read.is_active is True
