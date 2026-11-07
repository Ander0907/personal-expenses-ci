"""Health check router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_health_service
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "The database is unreachable.",
        }
    },
)
def health(
    response: Response,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    """Report API and database health.

    Args:
        response: Response used to set the status code.
        service: Service that probes the database.

    Returns:
        ``ok``/``ok`` with 200, or ``error``/``unavailable`` with 503.
    """
    if service.is_database_available():
        return HealthResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="error", database="unavailable")
