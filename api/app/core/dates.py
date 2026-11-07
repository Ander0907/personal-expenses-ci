"""Date helpers for month-based filtering."""

import re
from datetime import date

MIN_YEAR = 1
MAX_YEAR = 9998
_YEAR_MONTH = re.compile(r"([0-9]{4})-(0[1-9]|1[0-2])", re.ASCII)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Return the half-open date range covering a month.

    Args:
        year: Calendar year.
        month: Month number (1-12).

    Returns:
        The first day of the month and the first day of the next month.

    Raises:
        ValueError: If ``month`` is outside 1-12.
    """
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def parse_year_month(value: str) -> tuple[int, int]:
    """Parse a ``YYYY-MM`` string.

    Args:
        value: Text in ``YYYY-MM`` format.

    Returns:
        The year and month as integers.

    Raises:
        ValueError: If the text is not a valid ``YYYY-MM`` or the year is
            outside 1-9998 (so the next month is always representable).
    """
    match = _YEAR_MONTH.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid year-month: {value!r}")
    year = int(match.group(1))
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError(f"Year out of range: {value!r}")
    return year, int(match.group(2))
