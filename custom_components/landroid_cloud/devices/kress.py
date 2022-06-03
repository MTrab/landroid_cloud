"""Kress device definition."""
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

SUPPORTED_FEATURES = SUPPORT_LANDROID_BASE

class Button(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Kress button."""


class MowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Kress device."""

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES
