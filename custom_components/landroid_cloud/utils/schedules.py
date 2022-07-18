"""Utilities used by this module."""
# pylint: disable=relative-beyond-top-level
from __future__ import annotations

import re
from datetime import datetime

from homeassistant.exceptions import HomeAssistantError

TIME_REGEX = "(([0-9]){1,2}:([0-9]){2})"


def parseday(day: dict, data: dict) -> list:
    """Parse a schedule day."""
    result = []
    start = re.search(TIME_REGEX, data[day["start"]].replace(".", ":"))
    end = re.search(TIME_REGEX, data[day["end"]].replace(".", ":"))

    if start:
        start = start.group(1)
    else:
        raise HomeAssistantError(
            f"Wrong format in {day['start']}, needs to be HH:MM format"
        )

    if end:
        end = end.group(1)
    else:
        raise HomeAssistantError(
            f"Wrong format in {day['end']}, needs to be HH:MM format"
        )

    if day["boundary"] in data:
        boundary = bool(data[day["boundary"]])
    else:
        boundary = False

    result.append(start)
    time_start = datetime.strptime(start, "%H:%M")
    time_end = datetime.strptime(end, "%H:%M")
    runtime = (time_end - time_start).total_seconds() / 60
    result.append(int(runtime))
    result.append(int(boundary))

    if runtime == 0:
        result[0] = "00:00"
        result[2] = 0

    return result


def pass_thru(schedule, sunday_first: bool = True) -> list:
    """Parse primary schedule thru, before generating secondary schedule."""
    result = []

    if sunday_first:
        result.append(
            [
                schedule["sunday"]["start"],
                int(schedule["sunday"]["duration"]),
                int(schedule["sunday"]["boundary"]),
            ]
        )

    for day in schedule.items():
        if sunday_first and day[0] != "sunday":
            result.append(
                [day[1]["start"], int(day[1]["duration"]), int(day[1]["boundary"])]
            )

    return result
