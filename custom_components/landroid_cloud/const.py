"""Constants used by Landroid Cloud integration."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

from homeassistant.components.vacuum import (
    STATE_DOCKED,
    STATE_RETURNING,
    STATE_ERROR,
    STATE_PAUSED,
    STATE_IDLE,
)

from pyworxcloud.clouds import CLOUDS as api_clouds

# Startup banner
STARTUP = """
-------------------------------------------------------------------
Landroid Cloud integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/landroid_cloud/issues
-------------------------------------------------------------------
"""

# Some defaults
DEFAULT_NAME = "landroid"
DOMAIN = "landroid_cloud"
PLATFORM = "vacuum"
UPDATE_SIGNAL = "landroid_cloud_update"

# Service consts
SERVICE_POLL = "poll"
SERVICE_CONFIG = "config"
SERVICE_PARTYMODE = "partymode"
SERVICE_SETZONE = "setzone"
SERVICE_LOCK = "lock"
SERVICE_RESTART = "restart"
SERVICE_EDGECUT = "edgecut"
SERVICE_OTS = "ots"
SERVICE_SCHEDULE = "schedule"

# Extra states
STATE_INITIALIZING = "initializing"
STATE_OFFLINE = "offline"
STATE_RAINDELAY = "rain_delay"
STATE_MOWING = "mowing"
STATE_STARTING = "starting"
STATE_ZONING = "zoning"
STATE_EDGECUT = "edgecut"

# Service attributes
ATTR_MULTIZONE_DISTANCES = "multizone_distances"
ATTR_MULTIZONE_PROBABILITIES = "multizone_probabilities"
ATTR_RAINDELAY = "raindelay"
ATTR_TIMEEXTENSION = "timeextension"
ATTR_TORQUE = "torque"
ATTR_ZONE = "zone"
ATTR_BOUNDARY = "boundary"
ATTR_RUNTIME = "runtime"

# Attributes used for managing schedules
ATTR_TYPE = "type"
ATTR_MONDAY_START = "monday_start"
ATTR_MONDAY_END = "monday_end"
ATTR_MONDAY_BOUNDARY = "monday_boundary"
ATTR_TUESDAY_START = "tuesday_start"
ATTR_TUESDAY_END = "tuesday_end"
ATTR_TUESDAY_BOUNDARY = "tuesday_boundary"
ATTR_WEDNESDAY_START = "wednesday_start"
ATTR_WEDNESDAY_END = "wednesday_end"
ATTR_WEDNESDAY_BOUNDARY = "wednesday_boundary"
ATTR_THURSDAY_START = "thursday_start"
ATTR_THURSDAY_END = "thursday_end"
ATTR_THURSDAY_BOUNDARY = "thursday_boundary"
ATTR_FRIDAY_START = "friday_start"
ATTR_FRIDAY_END = "friday_end"
ATTR_FRIDAY_BOUNDARY = "friday_boundary"
ATTR_SATURDAY_START = "saturday_start"
ATTR_SATURDAY_END = "saturday_end"
ATTR_SATURDAY_BOUNDARY = "saturday_boundary"
ATTR_SUNDAY_START = "sunday_start"
ATTR_SUNDAY_END = "sunday_end"
ATTR_SUNDAY_BOUNDARY = "sunday_boundary"

# Available cloud vendors
CLOUDS = []
for cloud in api_clouds:
    CLOUDS.append(cloud.capitalize())

# State mapping
STATE_MAP = {
    0: STATE_IDLE,
    1: STATE_DOCKED,
    2: STATE_STARTING,
    3: STATE_STARTING,
    4: STATE_RETURNING,
    5: STATE_RETURNING,
    6: STATE_RETURNING,
    7: STATE_MOWING,
    8: STATE_ERROR,
    9: STATE_ERROR,
    10: STATE_ERROR,
    11: STATE_ERROR,
    12: STATE_MOWING,
    30: STATE_RETURNING,
    31: STATE_ZONING,
    32: STATE_EDGECUT,
    33: STATE_STARTING,
    34: STATE_PAUSED,
}


@dataclass
class ScheduleDays(IntEnum):
    """Schedule types."""

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


SCHEDULE_TYPE_MAP = {
    "primary": "d",
    "secondary": "dd",
}

SCHEDULE_TO_DAY = {
    "sunday": {
        "day": ScheduleDays.SUNDAY,
        "start": ATTR_SUNDAY_START,
        "end": ATTR_SUNDAY_END,
        "boundary": ATTR_SUNDAY_BOUNDARY,
        "clear": "sunday",
    },
    "monday": {
        "day": ScheduleDays.MONDAY,
        "start": ATTR_MONDAY_START,
        "end": ATTR_MONDAY_END,
        "boundary": ATTR_MONDAY_BOUNDARY,
        "clear": "monday",
    },
    "tuesday": {
        "day": ScheduleDays.TUESDAY,
        "start": ATTR_TUESDAY_START,
        "end": ATTR_TUESDAY_END,
        "boundary": ATTR_TUESDAY_BOUNDARY,
        "clear": "tuesday",
    },
    "wednesday": {
        "day": ScheduleDays.WEDNESDAY,
        "start": ATTR_WEDNESDAY_START,
        "end": ATTR_WEDNESDAY_END,
        "boundary": ATTR_WEDNESDAY_BOUNDARY,
        "clear": "wednesday",
    },
    "thursday": {
        "day": ScheduleDays.THURSDAY,
        "start": ATTR_THURSDAY_START,
        "end": ATTR_THURSDAY_END,
        "boundary": ATTR_THURSDAY_BOUNDARY,
        "clear": "thursday",
    },
    "friday": {
        "day": ScheduleDays.FRIDAY,
        "start": ATTR_FRIDAY_START,
        "end": ATTR_FRIDAY_END,
        "boundary": ATTR_FRIDAY_BOUNDARY,
        "clear": "friday",
    },
    "saturday": {
        "day": ScheduleDays.SATURDAY,
        "start": ATTR_SATURDAY_START,
        "end": ATTR_SATURDAY_END,
        "boundary": ATTR_SATURDAY_BOUNDARY,
        "clear": "saturday",
    },
}
