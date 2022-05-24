"""LandXcape device definition."""
from __future__ import annotations

import logging

from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import (
    LandroidCloudBase,
    SUPPORT_LANDROID_BASE,
)  # pylint: disable=relative-beyond-top-level

# from ..pyworxcloud import WorxCloud  # pylint: disable=relative-beyond-top-level


_LOGGER = logging.getLogger(__name__)

SUPPORT_LANDXCAPE = SUPPORT_LANDROID_BASE


class LandxcapeDevice(LandroidCloudBase, StateVacuumEntity):
    """Definition of Landxcape device."""

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_LANDXCAPE
