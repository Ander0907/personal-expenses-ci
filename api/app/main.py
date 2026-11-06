"""FastAPI application entry point."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A new ``FastAPI`` instance.
    """
    return FastAPI(title="Personal Expenses API", version="0.1.0")


app = create_app()
