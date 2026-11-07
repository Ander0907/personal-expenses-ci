"""Repository for expense persistence."""

import builtins
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.expense import Expense


@dataclass(frozen=True)
class CategoryTotal:
    """A category with its budget and spending over a period.

    Attributes:
        category_id: Category primary key.
        name: Category name.
        monthly_budget: Monthly budget of the category.
        total: Amount spent in the period (zero when nothing was spent).
    """

    category_id: int
    name: str
    monthly_budget: Decimal
    total: Decimal


class ExpenseRepository:
    """Reads and writes ``Expense`` rows."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used for all queries.
        """
        self._session = session

    def add(self, expense: Expense) -> Expense:
        """Persist a new expense.

        Args:
            expense: Transient expense to store.

        Returns:
            The stored, refreshed expense.
        """
        self._session.add(expense)
        self._session.commit()
        self._session.refresh(expense)
        return expense

    def get(self, expense_id: int) -> Expense | None:
        """Find an expense by primary key.

        Args:
            expense_id: Primary key to look up.

        Returns:
            The expense, or None.
        """
        return self._session.get(Expense, expense_id)

    def delete(self, expense: Expense) -> None:
        """Delete an expense and commit.

        Args:
            expense: Persistent expense to remove.
        """
        self._session.delete(expense)
        self._session.commit()

    def list(
        self,
        category_id: int | None,
        start: date | None,
        end: date | None,
        limit: int,
        offset: int,
    ) -> list[Expense]:
        """List expenses newest first.

        Args:
            category_id: Restrict to this category when not None.
            start: Inclusive lower date bound when not None.
            end: Exclusive upper date bound when not None.
            limit: Maximum number of rows.
            offset: Number of rows to skip.

        Returns:
            The requested page of expenses.
        """
        statement = select(Expense)
        if category_id is not None:
            statement = statement.where(Expense.category_id == category_id)
        if start is not None:
            statement = statement.where(Expense.spent_at >= start)
        if end is not None:
            statement = statement.where(Expense.spent_at < end)
        statement = (
            statement.order_by(Expense.spent_at.desc(), Expense.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [*self._session.scalars(statement)]

    def monthly_total(self, category_id: int, start: date, end: date) -> Decimal:
        """Sum a category's expenses over ``[start, end)`` in SQL.

        Args:
            category_id: Category to aggregate.
            start: Inclusive lower date bound.
            end: Exclusive upper date bound.

        Returns:
            The total, or ``Decimal('0')`` when nothing was spent.
        """
        statement = select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.category_id == category_id,
            Expense.spent_at >= start,
            Expense.spent_at < end,
        )
        return Decimal(self._session.scalar(statement) or 0)

    # ``builtins.list``: inside this class ``list`` is the method above.
    def totals_by_category(
        self, start: date, end: date
    ) -> builtins.list[CategoryTotal]:
        """Sum spending per category over ``[start, end)`` in one query.

        Every category is included, with a zero total when it has no expenses.

        Args:
            start: Inclusive lower date bound.
            end: Exclusive upper date bound.

        Returns:
            One row per category, ordered by name then id.
        """
        statement = (
            select(
                Category.id,
                Category.name,
                Category.monthly_budget,
                func.coalesce(func.sum(Expense.amount), 0),
            )
            .outerjoin(
                Expense,
                and_(
                    Expense.category_id == Category.id,
                    Expense.spent_at >= start,
                    Expense.spent_at < end,
                ),
            )
            .group_by(Category.id)
            .order_by(Category.name, Category.id)
        )
        return [
            CategoryTotal(category_id, name, budget, Decimal(total))
            for category_id, name, budget, total in self._session.execute(statement)
        ]
