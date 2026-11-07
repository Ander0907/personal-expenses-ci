"""Unit tests for ``app.core.error_handlers``.

A throwaway app with a single failing route proves the handler mapping.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import DomainError, DuplicateCategoryError


class TeapotError(DomainError):
    """Throwaway domain error with a custom status code."""

    status_code = 418


def test_any_domain_error_subclass_is_mapped_to_its_status_code() -> None:
    """A domain error subclass becomes a response with its own status code."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/teapot")
    def teapot() -> None:
        """Raise a throwaway domain error."""
        raise TeapotError("short and stout")

    response = TestClient(app).get("/teapot")

    assert response.status_code == 418
    assert response.json() == {"detail": "short and stout"}


def test_duplicate_category_error_is_mapped_to_409() -> None:
    """A raised duplicate category error becomes a 409 with a detail message."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        """Raise a duplicate category error."""
        raise DuplicateCategoryError("Food")

    response = TestClient(app).get("/boom")

    assert response.status_code == 409
    assert response.json() == {"detail": "Category 'Food' already exists"}
