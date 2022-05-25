"""Defines schedule classes."""

import calendar
from collections import namedtuple
from enum import IntEnum
import json


class ScheduleType(IntEnum):
    """Schedule types."""

    PRIMARY = 0
    SECONDARY = 1


TYPE_MAP = {ScheduleType.PRIMARY: "primary", ScheduleType.SECONDARY: "secondary"}


class Weekday:
    """Represents a weekday."""

    def __init__(self, weekday: str):
        """Initiate weekday."""
        self._name = weekday.lower()
        self._start = None
        self._duration = None
        self._boundary = False

    @property
    def todict(self) -> dict:
        """Return list object."""
        day = {
            "name": self._name,
            "settings": {
                "start": self._start,
                "duration": self._duration,
                "boundary": self._boundary,
            },
        }
        return day

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
        self.type = schedule_type
        self.weekdays = {}

        for day in list(calendar.day_name):
            newday = Weekday(day).todict
            self.weekdays[newday["name"]] = newday["settings"]

    @property
    def todict(self) -> dict:
        """Return list object."""
        val = {"type": self.type, "days": self.weekdays}
        return val
