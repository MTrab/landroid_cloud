"""LandXcape device definition."""
from __future__ import annotations

import logging

from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import LandroidCloudBase, SUPPORT_LANDROID # pylint: disable=relative-beyond-top-level
from ..pyworxcloud import WorxCloud # pylint: disable=relative-beyond-top-level


_LOGGER = logging.getLogger(__name__)


class LandxcapeDevice(LandroidCloudBase, StateVacuumEntity):
    """Definition of Landxcape device."""
