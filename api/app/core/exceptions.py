"""Domain exceptions raised by services and repositories."""

from datetime import date
from typing import ClassVar


class DomainError(Exception):
    """Base class for errors that represent a violated business rule.

    Attributes:
        status_code: HTTP status code used when the error reaches the API.
    """

    status_code: ClassVar[int] = 400


class DuplicateCategoryError(DomainError):
    """Raised when a category name is already in use."""

    status_code: ClassVar[int] = 409

    def __init__(self, name: str) -> None:
        """Initialize the error.

        Args:
            name: The category name that already exists.
        """
        super().__init__(f"Category '{name}' already exists")
        self.name = name


class CategoryNotFoundError(DomainError):
    """Raised when a category id does not exist."""

    status_code: ClassVar[int] = 404

    def __init__(self, category_id: int) -> None:
        """Initialize the error.

        Args:
            category_id: The id that was not found.
        """
        super().__init__(f"Category {category_id} not found")
        self.category_id = category_id


class InactiveCategoryError(DomainError):
    """Raised when an expense targets an inactive category."""

    status_code: ClassVar[int] = 422

    def __init__(self, category_id: int) -> None:
        """Initialize the error.

        Args:
            category_id: The inactive category id.
        """
        super().__init__(f"Category {category_id} is inactive")
        self.category_id = category_id


class FutureDateError(DomainError):
    """Raised when an expense is dated after today."""

    status_code: ClassVar[int] = 422

    def __init__(self, spent_at: date) -> None:
        """Initialize the error.

        Args:
            spent_at: The offending expense date.
        """
        super().__init__(f"Expense date {spent_at.isoformat()} is in the future")
        self.spent_at = spent_at


class InvalidMonthError(DomainError):
    """Raised when a month filter is not a valid ``YYYY-MM`` value."""

    status_code: ClassVar[int] = 422

    def __init__(self, value: str) -> None:
        """Initialize the error.

        Args:
            value: The offending month string.
        """
        super().__init__(
            f"Invalid month '{value}': expected YYYY-MM with year 0001-9998"
        )
        self.value = value


class ExpenseNotFoundError(DomainError):
    """Raised when an expense id does not exist."""

    status_code: ClassVar[int] = 404

    def __init__(self, expense_id: int) -> None:
        """Initialize the error.

        Args:
            expense_id: The id that was not found.
        """
        super().__init__(f"Expense {expense_id} not found")
        self.expense_id = expense_id
