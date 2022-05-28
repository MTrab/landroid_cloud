"""Constants used by Landroid Cloud integration."""
from __future__ import annotations

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

# Extra states
STATE_INITIALIZING = "initializing"
STATE_OFFLINE = "offline"
STATE_RAINDELAY = "rain_delay"
STATE_MOWING = "mowing"
STATE_STARTING = "starting"
STATE_ZONING = "zoning"
STATE_EDGECUT = "edgecut"

# Attributes
ATTR_MULTIZONE_DISTANCES = "multizone_distances"
ATTR_MULTIZONE_PROBABILITIES = "multizone_probabilities"
ATTR_RAINDELAY = "raindelay"
ATTR_TIMEEXTENSION = "timeextension"
ATTR_ZONE = "zone"
ATTR_BOUNDARY = "boundary"
ATTR_RUNTIME = "runtime"

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
