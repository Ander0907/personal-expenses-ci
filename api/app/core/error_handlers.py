"""Mapping of domain errors to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError


def _handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    """Translate a domain error into a JSON response.

    Args:
        request: The failing request (unused).
        exc: The raised ``DomainError``; its ``status_code`` is used.

    Returns:
        A JSON response with a ``detail`` message.
    """
    status_code = exc.status_code if isinstance(exc, DomainError) else 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers on the application.

    Args:
        app: Application to configure.
    """
    app.add_exception_handler(DomainError, _handle_domain_error)
