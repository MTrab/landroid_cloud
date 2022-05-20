"""Constants used by Landroid Cloud integration."""
from __future__ import annotations

# from pyworxcloud.clouds import CLOUDS as api_clouds
from .pyworxcloud.clouds import CLOUDS as api_clouds

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
UPDATE_SIGNAL = "landroid_cloud_update"

# Service consts
SERVICE_POLL = "poll"
SERVICE_START = "start"
SERVICE_PAUSE = "pause"
SERVICE_HOME = "home"
SERVICE_CONFIG = "config"
SERVICE_PARTYMODE = "partymode"
SERVICE_SETZONE = "setzone"
SERVICE_LOCK = "lock"
SERVICE_RESTART = "restart"
SERVICE_EDGECUT = "edgecut"

# Extra states
STATE_INITIALIZING = "Initializing"
STATE_OFFLINE = "Offline"

# Attributes
ATTR_ZONE = "zone"

# Available cloud vendors
CLOUDS = []
for cloud in api_clouds:
    CLOUDS.append(cloud.capitalize())
