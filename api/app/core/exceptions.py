"""Domain exceptions raised by services and repositories."""

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
