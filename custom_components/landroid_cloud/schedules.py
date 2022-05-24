"""Defines schedule classes."""

import calendar
from enum import IntEnum


class ScheduleType(IntEnum):
    """Schedule types."""

    PRIMARY = 0
    SECONDARY = 1


class Weekday:
    """Represents a weekday."""

    def __init__(self, weekday: str):
        """Initiate weekday."""
        self._name = weekday
        self._start = None
        self._duration = None
        self._boundary = False

    @property
    def name(self) -> str:
        """Return weekday name."""
        return self._name

    @property
    def start(self) -> str:
        """Return start time."""
        return self._start

    @property
    def duration(self) -> int:
        """Return duration."""
        return self._duration

    @property
    def boundary(self) -> bool:
        """Do boundary (edge) cut."""
        return self._boundary


class Schedule:
    """Represents a schedule."""

    def __init__(self, schedule_type: ScheduleType):
        """Initiate a new schedule."""
        self._type = schedule_type
        self._weekdays = {}

        for weekday in list(calendar.day_name):
            self._weekdays.update(Weekday(weekday))

    @property
    def schedule(self) -> ScheduleType:
        """Return schedule type."""
        return self._type

    @property
    def weekdays(self) -> dict(Weekday):
        """Return dict of weekdays."""
        return self._weekdays
