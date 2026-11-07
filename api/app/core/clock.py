"""Injectable clock so time-dependent rules are testable."""

from datetime import date
from typing import Protocol


class Clock(Protocol):
    """Source of the current date."""

    def today(self) -> date:
        """Return the current date.

        Returns:
            Today's date.
        """
        ...


class SystemClock:
    """Clock backed by the system date.

    Uses the container's local date, which is UTC in the Docker image.
    """

    def today(self) -> date:
        """Return the current system date.

        Returns:
            Today's date.
        """
        return date.today()
