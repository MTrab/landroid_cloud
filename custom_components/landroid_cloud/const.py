"""Constants for the Landroid Cloud integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "landroid_cloud"

PLATFORMS: list[Platform] = [
    Platform.LAWN_MOWER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
]

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
