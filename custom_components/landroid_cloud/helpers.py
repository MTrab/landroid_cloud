"""Helpers for Landroid Cloud integration."""

from homeassistant.backports.enum import StrEnum

from .const import ATTR_NEXT_ZONE, SERVICE_EDGECUT, SERVICE_RESTART


class LandroidButtonTypes(StrEnum):
    """Defines different button types for Landroid Cloud integration."""

    RESTART = SERVICE_RESTART
    EDGECUT = SERVICE_EDGECUT

class LandroidSelectTypes(StrEnum):
    """Defines different button types for Landroid Cloud integration."""

    NEXT_ZONE = ATTR_NEXT_ZONE
