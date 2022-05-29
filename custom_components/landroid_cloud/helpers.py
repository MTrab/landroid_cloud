"""Helpers for Landroid Cloud integration."""

from homeassistant.backports.enum import StrEnum

from .const import SERVICE_EDGECUT, SERVICE_RESTART


class LandroidButtonTypes(StrEnum):
    """Defines different button types for Landroid Cloud integration."""

    RESTART = SERVICE_RESTART
    EDGECUT = SERVICE_EDGECUT
