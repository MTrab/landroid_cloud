"""Constants for the Landroid Cloud integration."""

from __future__ import annotations

from enum import StrEnum

DOMAIN = "landroid_cloud"

PLATFORMS = [
    "lawn_mower",
    "sensor",
    "binary_sensor",
    "switch",
    "button",
    "number",
    "select",
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
