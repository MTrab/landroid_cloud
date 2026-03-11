"""Constants for the Landroid Cloud integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "landroid_cloud"

PLATFORMS: list[Platform] = [
    Platform.LAWN_MOWER,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]

STARTUP = """
-------------------------------------------------------------------
Landroid Cloud integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/landroid_cloud/issues
-------------------------------------------------------------------
"""

CONF_CLOUD = "cloud"
CONF_COMMAND_TIMEOUT = "command_timeout"

DEFAULT_CLOUD = "worx"
DEFAULT_COMMAND_TIMEOUT = 30.0
MIN_COMMAND_TIMEOUT = 1.0
MAX_COMMAND_TIMEOUT = 120.0


class CloudProvider(StrEnum):
    """Supported cloud providers."""

    WORX = "worx"
    KRESS = "kress"
    LANDXCAPE = "landxcape"
