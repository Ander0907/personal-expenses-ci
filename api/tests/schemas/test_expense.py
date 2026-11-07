"""Unit tests for ``app.schemas.expense``."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseCreated, ExpenseRead


def make_payload(**overrides: object) -> dict[str, Any]:
    """Build a valid creation payload with optional overrides.

    Args:
        **overrides: Fields replacing the defaults.

    Returns:
        A dictionary accepted by ``ExpenseCreate``.
    """
    payload: dict[str, Any] = {
        "category_id": 1,
        "amount": "25.50",
        "description": "Lunch",
        "spent_at": "2026-11-05",
    }
    payload.update(overrides)
    return payload


def make_expense() -> Expense:
    """Build an in-memory expense as loaded from the database.

    Returns:
        An ``Expense`` with every field set.
    """
    return Expense(
        id=7,
        category_id=1,
        amount=Decimal("25.50"),
        description="Lunch",
        spent_at=date(2026, 11, 5),
        created_at=datetime(2026, 11, 5, 12, 0, tzinfo=UTC),
    )


def test_expense_create_accepts_a_valid_payload() -> None:
    """Expense create parses every field into its typed value."""
    data = ExpenseCreate.model_validate(make_payload())

    assert data.category_id == 1
    assert data.amount == Decimal("25.50")
    assert data.description == "Lunch"
    assert data.spent_at == date(2026, 11, 5)


def test_expense_create_accepts_the_minimum_amount() -> None:
    """Expense create accepts an amount of exactly 0.01."""
    data = ExpenseCreate.model_validate(make_payload(amount="0.01"))

    assert data.amount == Decimal("0.01")


def test_expense_create_defaults_description_to_none() -> None:
    """Expense create treats a missing description as None."""
    payload = make_payload()
    del payload["description"]

    assert ExpenseCreate.model_validate(payload).description is None


def test_expense_create_strips_the_description() -> None:
    """Expense create strips surrounding whitespace from the description."""
    data = ExpenseCreate.model_validate(make_payload(description="  Lunch  "))

    assert data.description == "Lunch"


@pytest.mark.parametrize("blank", ["", "   "])
def test_expense_create_turns_a_blank_description_into_none(blank: str) -> None:
    """Expense create normalizes blank descriptions to None."""
    data = ExpenseCreate.model_validate(make_payload(description=blank))

    assert data.description is None


def test_expense_create_accepts_a_null_description() -> None:
    """Expense create accepts an explicit null description."""
    data = ExpenseCreate.model_validate(make_payload(description=None))

    assert data.description is None


def test_expense_create_accepts_a_description_of_255_characters() -> None:
    """Expense create accepts the maximum description length."""
    data = ExpenseCreate.model_validate(make_payload(description="a" * 255))

    assert data.description == "a" * 255


@pytest.mark.parametrize(
    "overrides",
    [
        {"category_id": 0},
        {"category_id": -1},
        {"amount": "0"},
        {"amount": "-1"},
        {"amount": "10.123"},
        {"amount": "1234567890123"},
        {"description": "a" * 256},
        {"description": "a\u0000b"},
        {"description": "line\nbreak"},
        {"spent_at": "not-a-date"},
        {"id": 5},
    ],
    ids=[
        "category-zero",
        "category-negative",
        "amount-zero",
        "amount-negative",
        "three-decimals",
        "too-many-digits",
        "description-too-long",
        "null-character",
        "newline",
        "bad-date",
        "extra-field",
    ],
)
def test_expense_create_rejects_invalid_values(overrides: dict[str, Any]) -> None:
    """Expense create raises a validation error for invalid input."""
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(make_payload(**overrides))


def test_expense_create_accepts_the_maximum_category_id() -> None:
    """Expense create accepts the PostgreSQL int4 maximum as category id."""
    data = ExpenseCreate.model_validate(make_payload(category_id=2_147_483_647))

    assert data.category_id == 2_147_483_647


def test_expense_create_rejects_a_category_id_above_int4() -> None:
    """Expense create rejects a category id overflowing PostgreSQL ``integer``."""
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(make_payload(category_id=2_147_483_648))


@pytest.mark.parametrize("missing", ["category_id", "amount", "spent_at"])
def test_expense_create_requires_mandatory_fields(missing: str) -> None:
    """Expense create rejects payloads lacking a mandatory field."""
    payload = make_payload()
    del payload[missing]

    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(payload)


def test_expense_read_builds_from_an_orm_object() -> None:
    """Expense read serializes attributes of an ``Expense``."""
    read = ExpenseRead.model_validate(make_expense())

    assert read.id == 7
    assert read.category_id == 1
    assert read.amount == Decimal("25.50")
    assert read.description == "Lunch"
    assert read.spent_at == date(2026, 11, 5)
    assert read.created_at == datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


def test_expense_created_extends_expense_read_with_over_budget() -> None:
    """Expense created adds the ``over_budget`` flag to the read schema."""
    created = ExpenseCreated(
        **ExpenseRead.model_validate(make_expense()).model_dump(),
        over_budget=True,
    )

    assert issubclass(ExpenseCreated, ExpenseRead)
    assert created.over_budget is True
    assert created.id == 7
