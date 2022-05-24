"""Kress device definition."""
from __future__ import annotations

import logging

from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import (
    LandroidCloudBase,
    SUPPORT_LANDROID_BASE,
)  # pylint: disable=relative-beyond-top-level

# from ..pyworxcloud import WorxCloud # pylint: disable=relative-beyond-top-level

_LOGGER = logging.getLogger(__name__)

SUPPORT_KRESS = SUPPORT_LANDROID_BASE


class KressDevice(LandroidCloudBase, StateVacuumEntity):
    """Definition of Kress device."""

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_KRESS
