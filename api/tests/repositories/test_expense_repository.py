"""Unit tests for ``app.repositories.expense_repository``.

The session is a mock; statements are inspected by compiling them to SQL for
the PostgreSQL dialect (never executed).
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import ClauseElement

from app.models.expense import Expense
from app.repositories.expense_repository import ExpenseRepository


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


def make_expense() -> Expense:
    """Build an in-memory expense.

    Returns:
        A transient ``Expense``.
    """
    return Expense(category_id=1, amount=Decimal("10.00"), spent_at=date(2026, 11, 5))


def list_sql(**filters: object) -> str:
    """Run ``list`` against a mock session and return the compiled SQL.

    Args:
        **filters: Keyword overrides for the repository ``list`` call.

    Returns:
        The SQL of the statement handed to ``session.scalars``.
    """
    session = MagicMock()
    session.scalars.return_value = []
    arguments: dict[str, object] = {
        "category_id": None,
        "start": None,
        "end": None,
        "limit": 100,
        "offset": 0,
    }
    arguments.update(filters)
    ExpenseRepository(session).list(**arguments)
    return compile_sql(session.scalars.call_args.args[0])


def test_add_persists_commits_refreshes_and_returns_the_expense() -> None:
    """Add stores the expense and returns the refreshed instance."""
    session = MagicMock()
    expense = make_expense()

    result = ExpenseRepository(session).add(expense)

    assert result is expense
    session.add.assert_called_once_with(expense)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(expense)


def test_get_returns_the_expense_found_by_primary_key() -> None:
    """Get looks the expense up with ``session.get``."""
    session = MagicMock()
    expense = make_expense()
    session.get.return_value = expense

    result = ExpenseRepository(session).get(7)

    assert result is expense
    session.get.assert_called_once_with(Expense, 7)


def test_get_returns_none_when_the_expense_is_absent() -> None:
    """Get returns None when the primary key matches nothing."""
    session = MagicMock()
    session.get.return_value = None

    assert ExpenseRepository(session).get(7) is None


def test_delete_removes_the_expense_and_commits() -> None:
    """Delete removes the instance and commits afterwards."""
    session = MagicMock()
    expense = make_expense()

    ExpenseRepository(session).delete(expense)

    session.delete.assert_called_once_with(expense)
    session.commit.assert_called_once_with()
    names = [call[0] for call in session.method_calls]
    assert names.index("delete") < names.index("commit")


def test_list_returns_the_scalars_as_a_list() -> None:
    """List materializes the session result into a list."""
    session = MagicMock()
    first, second = make_expense(), make_expense()
    session.scalars.return_value = iter([first, second])

    result = ExpenseRepository(session).list(
        category_id=None, start=None, end=None, limit=10, offset=0
    )

    assert result == [first, second]
    session.scalars.assert_called_once()


def test_list_without_filters_has_no_where_clause() -> None:
    """List applies no filter when category and period are absent."""
    assert "WHERE" not in list_sql()


def test_list_filters_by_category() -> None:
    """List restricts to the given category."""
    assert "expenses.category_id = 3" in list_sql(category_id=3)


def test_list_filters_by_half_open_period() -> None:
    """List includes ``start`` and excludes ``end``."""
    sql = list_sql(start=date(2026, 11, 1), end=date(2026, 12, 1))

    assert (
        "expenses.spent_at >= '2026-11-01' AND expenses.spent_at < '2026-12-01'" in sql
    )


def test_list_orders_newest_first_with_limit_and_offset() -> None:
    """List builds a deterministic, paginated statement."""
    sql = list_sql(limit=10, offset=20)

    assert "ORDER BY expenses.spent_at DESC, expenses.id DESC" in sql
    assert "LIMIT 10 OFFSET 20" in sql


def test_monthly_total_returns_the_scalar_as_a_decimal() -> None:
    """Monthly total returns the summed amount."""
    session = MagicMock()
    session.scalar.return_value = Decimal("42.50")

    result = ExpenseRepository(session).monthly_total(
        3, date(2026, 11, 1), date(2026, 12, 1)
    )

    assert result == Decimal("42.50")
    assert isinstance(result, Decimal)
    session.scalar.assert_called_once()


@pytest.mark.parametrize("raw", [None, 0, Decimal("0")], ids=["none", "int", "decimal"])
def test_monthly_total_converts_empty_sums_to_decimal_zero(raw: object) -> None:
    """Monthly total yields ``Decimal('0')`` when nothing was spent."""
    session = MagicMock()
    session.scalar.return_value = raw

    result = ExpenseRepository(session).monthly_total(
        3, date(2026, 11, 1), date(2026, 12, 1)
    )

    assert result == Decimal("0")
    assert isinstance(result, Decimal)


def test_monthly_total_sums_amounts_for_the_category_and_period() -> None:
    """Monthly total sums with coalesce over the category and [start, end)."""
    session = MagicMock()
    session.scalar.return_value = None

    ExpenseRepository(session).monthly_total(3, date(2026, 11, 1), date(2026, 12, 1))

    sql = compile_sql(session.scalar.call_args.args[0])
    assert "coalesce(sum(expenses.amount), 0)" in sql
    assert "expenses.category_id = 3" in sql
    assert (
        "expenses.spent_at >= '2026-11-01' AND expenses.spent_at < '2026-12-01'" in sql
    )
