"""Unit tests for ``app.core.exceptions``."""

from datetime import date

from app.core.exceptions import (
    CategoryNotFoundError,
    DomainError,
    DuplicateCategoryError,
    ExpenseNotFoundError,
    FutureDateError,
    InactiveCategoryError,
    InvalidMonthError,
)


def test_duplicate_category_error_is_a_domain_error() -> None:
    """Duplicate category error specializes the domain error base."""
    assert issubclass(DuplicateCategoryError, DomainError)
    assert issubclass(DomainError, Exception)


def test_domain_error_defaults_to_status_code_400() -> None:
    """Domain error maps to 400 unless a subclass says otherwise."""
    assert DomainError.status_code == 400


def test_duplicate_category_error_has_status_code_409() -> None:
    """Duplicate category error maps to 409 Conflict."""
    assert DuplicateCategoryError.status_code == 409


def test_duplicate_category_error_exposes_the_offending_name() -> None:
    """Duplicate category error keeps the name it was built with."""
    error = DuplicateCategoryError("Food")

    assert error.name == "Food"


def test_duplicate_category_error_message_mentions_the_name() -> None:
    """Duplicate category error renders a readable message."""
    error = DuplicateCategoryError("Food")

    assert str(error) == "Category 'Food' already exists"


def test_category_not_found_error_is_a_404_domain_error() -> None:
    """Category not found error maps to 404 and keeps the id."""
    error = CategoryNotFoundError(5)

    assert isinstance(error, DomainError)
    assert CategoryNotFoundError.status_code == 404
    assert error.category_id == 5
    assert str(error) == "Category 5 not found"


def test_inactive_category_error_is_a_422_domain_error() -> None:
    """Inactive category error maps to 422 and keeps the id."""
    error = InactiveCategoryError(5)

    assert isinstance(error, DomainError)
    assert InactiveCategoryError.status_code == 422
    assert error.category_id == 5
    assert str(error) == "Category 5 is inactive"


def test_future_date_error_is_a_422_domain_error() -> None:
    """Future date error maps to 422 and renders the ISO date."""
    error = FutureDateError(date(2026, 12, 1))

    assert isinstance(error, DomainError)
    assert FutureDateError.status_code == 422
    assert error.spent_at == date(2026, 12, 1)
    assert str(error) == "Expense date 2026-12-01 is in the future"


def test_invalid_month_error_is_a_422_domain_error() -> None:
    """Invalid month error maps to 422, keeps the value and explains the format."""
    error = InvalidMonthError("0000-05")

    assert isinstance(error, DomainError)
    assert InvalidMonthError.status_code == 422
    assert error.value == "0000-05"
    assert str(error) == (
        "Invalid month '0000-05': expected YYYY-MM with year 0001-9998"
    )


def test_expense_not_found_error_is_a_404_domain_error() -> None:
    """Expense not found error maps to 404 and keeps the id."""
    error = ExpenseNotFoundError(9)

    assert isinstance(error, DomainError)
    assert ExpenseNotFoundError.status_code == 404
    assert error.expense_id == 9
    assert str(error) == "Expense 9 not found"
