"""Business rules for categories."""

from app.core.exceptions import DuplicateCategoryError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate


class CategoryService:
    """Creates and lists categories."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used for persistence.
        """
        self._repository = repository

    def create(self, data: CategoryCreate) -> Category:
        """Create a category with a case-insensitively unique name.

        Args:
            data: Validated creation payload.

        Returns:
            The stored category.

        Raises:
            DuplicateCategoryError: If the name is already taken.
        """
        if self._repository.get_by_name_case_insensitive(data.name) is not None:
            raise DuplicateCategoryError(data.name)
        category = Category(
            name=data.name,
            monthly_budget=data.monthly_budget,
            is_active=data.is_active,
        )
        return self._repository.add(category)

    def list(self, limit: int, offset: int) -> list[Category]:
        """List categories.

        Args:
            limit: Maximum number of categories.
            offset: Number of categories to skip.

        Returns:
            The requested page of categories.
        """
        return self._repository.list(limit=limit, offset=offset)
