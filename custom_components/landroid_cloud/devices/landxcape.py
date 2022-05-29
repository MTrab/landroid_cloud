"""LandXcape device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import (
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    SUPPORT_LANDROID_BASE,
)

# from pyworxcloud import WorxCloud


_LOGGER = logging.getLogger(__name__)

SUPPORT_LANDXCAPE = SUPPORT_LANDROID_BASE


class LandxcapeButton(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Landxcape button."""


class LandxcapeMowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Landxcape device."""

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_LANDXCAPE
