"""Unit tests for ``app.core.clock``."""

from datetime import date
from typing import Protocol
from unittest.mock import patch

from app.core.clock import Clock, SystemClock


def test_system_clock_returns_the_current_date() -> None:
    """System clock delegates to ``date.today``."""
    with patch("app.core.clock.date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 6)

        assert SystemClock().today() == date(2026, 11, 6)


def test_clock_is_a_protocol() -> None:
    """Clock is declared as a ``typing.Protocol``."""
    assert Protocol in Clock.__bases__


def test_system_clock_satisfies_the_clock_protocol() -> None:
    """System clock can be used wherever a ``Clock`` is expected."""
    clock: Clock = SystemClock()

    assert isinstance(clock.today(), date)
