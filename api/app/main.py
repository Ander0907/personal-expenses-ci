"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A new ``FastAPI`` instance with all routers included.
    """
    application = FastAPI(title="Personal Expenses API", version="0.1.0")
    application.include_router(health.router)
    return application


app = create_app()
