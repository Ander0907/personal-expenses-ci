"""Schemas for the health endpoint."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check payload.

    Attributes:
        status: Overall service status.
        database: Database connectivity status.
    """

    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]
