"""Unit tests for ``app.core.exceptions``."""

from app.core.exceptions import DomainError, DuplicateCategoryError


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
