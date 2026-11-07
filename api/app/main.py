"""FastAPI application entry point."""

from fastapi import FastAPI

from app.core.error_handlers import register_exception_handlers
from app.routers import categories, health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A new ``FastAPI`` instance with all routers included.
    """
    application = FastAPI(title="Personal Expenses API", version="0.1.0")
    register_exception_handlers(application)
    application.include_router(health.router)
    application.include_router(categories.router)
    return application


app = create_app()
