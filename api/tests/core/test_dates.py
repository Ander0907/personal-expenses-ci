"""Unit tests for ``app.core.dates``."""

from datetime import date

import pytest

from app.core.dates import month_bounds, parse_year_month


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [
        (2026, 11, (date(2026, 11, 1), date(2026, 12, 1))),
        (2026, 1, (date(2026, 1, 1), date(2026, 2, 1))),
        (2026, 12, (date(2026, 12, 1), date(2027, 1, 1))),
        (2024, 2, (date(2024, 2, 1), date(2024, 3, 1))),
    ],
    ids=["november", "january", "december-rolls-year", "leap-february"],
)
def test_month_bounds_returns_first_day_and_exclusive_end(
    year: int, month: int, expected: tuple[date, date]
) -> None:
    """Month bounds are the first day and the first day of the next month."""
    assert month_bounds(year, month) == expected


@pytest.mark.parametrize("month", [0, 13, -1])
def test_month_bounds_rejects_an_invalid_month(month: int) -> None:
    """Month bounds raises ``ValueError`` for months outside 1-12."""
    with pytest.raises(ValueError):
        month_bounds(2026, month)


def test_parse_year_month_returns_year_and_month() -> None:
    """Parse year month splits ``YYYY-MM`` into integers."""
    assert parse_year_month("2026-11") == (2026, 11)


@pytest.mark.parametrize(
    "value",
    ["2026-13", "2026-00", "26-11", "2026/11", "", "2026-1", "abc"],
)
def test_parse_year_month_rejects_malformed_values(value: str) -> None:
    """Parse year month raises ``ValueError`` for anything but ``YYYY-MM``."""
    with pytest.raises(ValueError):
        parse_year_month(value)


@pytest.mark.parametrize(
    "value",
    ["0000-05", "9999-12", "٢٠٢٦-11"],
    ids=["year-zero", "year-9999", "non-ascii-digits"],
)
def test_parse_year_month_rejects_unsupported_years_and_digits(value: str) -> None:
    """Parse year month rejects years outside 1-9998 and non-ASCII digits."""
    with pytest.raises(ValueError):
        parse_year_month(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("0001-01", (1, 1)), ("9998-12", (9998, 12))],
    ids=["first-supported", "last-supported"],
)
def test_parse_year_month_accepts_the_supported_year_range(
    value: str, expected: tuple[int, int]
) -> None:
    """Parse year month accepts the first and last supported months."""
    assert parse_year_month(value) == expected


def test_month_bounds_handles_the_last_supported_year() -> None:
    """Month bounds for December 9998 ends on January 9999."""
    assert month_bounds(9998, 12) == (date(9998, 12, 1), date(9999, 1, 1))
