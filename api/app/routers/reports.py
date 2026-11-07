"""Report router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dates import MAX_YEAR, MIN_YEAR
from app.dependencies import get_report_service
from app.schemas.report import MonthlyReport
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


@router.get(
    "/monthly",
    response_model=MonthlyReport,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Invalid year or month."}
    },
)
def monthly_report(
    service: ReportServiceDep,
    year: Annotated[int, Query(ge=MIN_YEAR, le=MAX_YEAR)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> MonthlyReport:
    """Return the spending report for a month.

    Args:
        service: Report service.
        year: Calendar year (1-9998).
        month: Month number (1-12).

    Returns:
        Per-category totals and the month total.
    """
    return service.monthly(year=year, month=month)
