"""LandXcape device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging

from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import (
    LandroidCloudVacuumBase,
    SUPPORT_LANDROID_BASE,
)

# from pyworxcloud import WorxCloud


_LOGGER = logging.getLogger(__name__)

SUPPORT_LANDXCAPE = SUPPORT_LANDROID_BASE


class LandxcapeDevice(LandroidCloudVacuumBase, StateVacuumEntity):
    """Definition of Landxcape device."""

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_LANDXCAPE
