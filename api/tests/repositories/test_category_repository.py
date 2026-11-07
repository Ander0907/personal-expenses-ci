"""Unit tests for ``app.repositories.category_repository``.

The session is a mock; statements are inspected by compiling them to SQL for
the PostgreSQL dialect (never executed).
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import ClauseElement

from app.core.exceptions import DuplicateCategoryError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository


def compile_sql(statement: ClauseElement) -> str:
    """Compile a statement to PostgreSQL SQL with literal values inlined.

    Args:
        statement: The statement captured from the mock session.

    Returns:
        The SQL text.
    """
    return str(
        statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def make_category(name: str = "Food") -> Category:
    """Build an in-memory category.

    Args:
        name: Category name.

    Returns:
        A transient ``Category``.
    """
    return Category(name=name, monthly_budget=Decimal("10.00"), is_active=True)


class FakeDiag:
    """Stand-in for the driver diagnostic object."""

    def __init__(self, constraint_name: str) -> None:
        """Store the constraint name.

        Args:
            constraint_name: Name reported by the driver.
        """
        self.constraint_name = constraint_name


class FakeDriverError(Exception):
    """Stand-in for the driver exception wrapped by ``IntegrityError``."""

    def __init__(self, message: str, diag: FakeDiag | None = None) -> None:
        """Build the error, attaching ``diag`` only when given.

        Args:
            message: Driver message text.
            diag: Optional diagnostic carrying the constraint name.
        """
        super().__init__(message)
        if diag is not None:
            self.diag = diag


def integrity_error(
    constraint: str, message: str = "integrity violation"
) -> IntegrityError:
    """Build an ``IntegrityError`` whose driver diagnostic names a constraint.

    Args:
        constraint: Constraint name reported in ``orig.diag.constraint_name``.
        message: Driver message text.

    Returns:
        The exception.
    """
    return IntegrityError(
        "INSERT ...", {}, FakeDriverError(message, FakeDiag(constraint))
    )


def test_get_by_name_case_insensitive_returns_the_scalar_result() -> None:
    """Lookup returns whatever the session yields for the statement."""
    session = MagicMock()
    category = make_category()
    session.scalar.return_value = category

    result = CategoryRepository(session).get_by_name_case_insensitive("food")

    assert result is category
    session.scalar.assert_called_once()


def test_get_by_name_case_insensitive_returns_none_when_absent() -> None:
    """Lookup returns None when no category matches."""
    session = MagicMock()
    session.scalar.return_value = None

    assert CategoryRepository(session).get_by_name_case_insensitive("x") is None


def test_get_by_name_case_insensitive_compares_lowercased_names() -> None:
    """Lookup filters on ``lower(categories.name) = lower(value)``."""
    session = MagicMock()

    CategoryRepository(session).get_by_name_case_insensitive("Food")

    sql = compile_sql(session.scalar.call_args.args[0])
    assert "lower(categories.name) = lower('Food')" in sql


def test_add_persists_commits_refreshes_and_returns_the_category() -> None:
    """Add stores the category and returns the refreshed instance."""
    session = MagicMock()
    category = make_category()

    result = CategoryRepository(session).add(category)

    assert result is category
    session.add.assert_called_once_with(category)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(category)


def test_add_rolls_back_and_raises_duplicate_on_unique_name_violation() -> None:
    """Add maps a ``uq_categories_name`` violation to a domain error."""
    session = MagicMock()
    session.commit.side_effect = integrity_error("uq_categories_name")

    with pytest.raises(DuplicateCategoryError) as raised:
        CategoryRepository(session).add(make_category("Food"))

    assert raised.value.name == "Food"
    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()


def test_add_rolls_back_and_reraises_other_integrity_errors() -> None:
    """Add re-raises integrity errors unrelated to the name constraint."""
    session = MagicMock()
    error = integrity_error("monthly_budget_non_negative")
    session.commit.side_effect = error

    with pytest.raises(IntegrityError) as raised:
        CategoryRepository(session).add(make_category())

    assert raised.value is error
    session.rollback.assert_called_once_with()


def test_add_reraises_when_only_the_message_text_mentions_the_constraint() -> None:
    """Add trusts the diagnostic, never the message text."""
    session = MagicMock()
    error = integrity_error(
        "some_other_constraint",
        message='violates unique constraint "uq_categories_name"',
    )
    session.commit.side_effect = error

    with pytest.raises(IntegrityError) as raised:
        CategoryRepository(session).add(make_category())

    assert raised.value is error
    session.rollback.assert_called_once_with()


def test_add_reraises_when_the_driver_error_has_no_diagnostic() -> None:
    """Add re-raises integrity errors whose driver error lacks ``diag``."""
    session = MagicMock()
    error = IntegrityError(
        "INSERT ...", {}, FakeDriverError('unique constraint "uq_categories_name"')
    )
    session.commit.side_effect = error

    with pytest.raises(IntegrityError) as raised:
        CategoryRepository(session).add(make_category())

    assert raised.value is error
    session.rollback.assert_called_once_with()


def test_list_returns_the_scalars_as_a_list() -> None:
    """List materializes the session result into a list."""
    session = MagicMock()
    first, second = make_category("A"), make_category("B")
    session.scalars.return_value = iter([first, second])

    result = CategoryRepository(session).list(limit=10, offset=20)

    assert result == [first, second]
    session.scalars.assert_called_once()


def test_list_orders_by_name_then_id_with_limit_and_offset() -> None:
    """List builds a deterministic, paginated statement."""
    session = MagicMock()
    session.scalars.return_value = []

    CategoryRepository(session).list(limit=10, offset=20)

    sql = compile_sql(session.scalars.call_args.args[0])
    assert "ORDER BY categories.name, categories.id" in sql
    assert "LIMIT 10 OFFSET 20" in sql
