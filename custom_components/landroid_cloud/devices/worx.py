"""Worx Landroid device definition."""
from __future__ import annotations

import logging

from functools import partial

from homeassistant.components.vacuum import StateVacuumEntity

from ..device_base import LandroidCloudBase, SUPPORT_LANDROID # pylint: disable=relative-beyond-top-level
from ..pyworxcloud import WorxCloud # pylint: disable=relative-beyond-top-level


_LOGGER = logging.getLogger(__name__)


class WorxDevice(LandroidCloudBase, StateVacuumEntity):
    """Definition of Worx Landroid device."""

    # def __init__(self, hass, api):
    #     """Init new base device."""
    #     super().__init__(hass, api)
    #     device: WorxCloud = self.api.device

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_LANDROID

    async def async_toggle_lock(self):
        """Toggle locked state."""
        device: WorxCloud = self.api.device
        set_lock = not bool(device.locked)
        _LOGGER.debug("Setting locked state for %s to %s", self._name, set_lock)
        await self.hass.async_add_executor_job(partial(device.lock, set_lock))

    async def async_toggle_partymode(self):
        """Toggle partymode state."""
        device: WorxCloud = self.api.device
        set_partymode = not bool(device.partymode_enabled)
        _LOGGER.debug("Setting PartyMode to %s on %s", set_partymode, self._name)
        await self.hass.async_add_executor_job(
            partial(device.enable_partymode, set_partymode)
        )

    async def async_edgecut(self):
        """Start edgecut routine."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Starting edgecut routine for %s", self._name)
        await self.hass.async_add_executor_job(device.edgecut)

