"""Repository for category persistence."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateCategoryError
from app.models.category import Category

UNIQUE_NAME_CONSTRAINT = "uq_categories_name"


class CategoryRepository:
    """Reads and writes ``Category`` rows.

    Note:
        The case-insensitive uniqueness rule is enforced in the service. The
        database unique constraint is exact-case, so two concurrent requests
        differing only by case could both succeed (accepted residual risk;
        no schema change by decision).
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used for all queries.
        """
        self._session = session

    def get_by_name_case_insensitive(self, name: str) -> Category | None:
        """Find a category whose name matches ignoring case.

        Args:
            name: Name to look up.

        Returns:
            The matching category, or None.
        """
        statement = select(Category).where(
            func.lower(Category.name) == func.lower(name)
        )
        return self._session.scalar(statement)

    def add(self, category: Category) -> Category:
        """Persist a new category.

        Args:
            category: Transient category to store.

        Returns:
            The stored, refreshed category.

        Raises:
            DuplicateCategoryError: If the unique name constraint is violated.
            sqlalchemy.exc.IntegrityError: For any other integrity violation.
        """
        self._session.add(category)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            diag = getattr(error.orig, "diag", None)
            if getattr(diag, "constraint_name", None) == UNIQUE_NAME_CONSTRAINT:
                raise DuplicateCategoryError(category.name) from error
            raise
        self._session.refresh(category)
        return category

    def list(self, limit: int, offset: int) -> list[Category]:
        """List categories ordered by name, then id.

        Args:
            limit: Maximum number of rows.
            offset: Number of rows to skip.

        Returns:
            The requested page of categories.
        """
        statement = (
            select(Category)
            .order_by(Category.name, Category.id)
            .limit(limit)
            .offset(offset)
        )
        return [*self._session.scalars(statement)]
