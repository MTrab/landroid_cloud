"""Worx Landroid device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations
import json

import logging

from functools import partial
import voluptuous as vol

from homeassistant.components.button import ButtonEntity
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError

from pyworxcloud import (
    NoOneTimeScheduleError,
    NoPartymodeError,
    WorxCloud,
)

from ..const import (
    ATTR_BOUNDARY,
    ATTR_MULTIZONE_DISTANCES,
    ATTR_MULTIZONE_PROBABILITIES,
    ATTR_RAINDELAY,
    ATTR_RUNTIME,
    ATTR_TIMEEXTENSION,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_OTS,
    SERVICE_PARTYMODE,
    SERVICE_RESTART,
    SERVICE_SETZONE,
)

from ..device_base import (
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    SUPPORT_LANDROID_BASE,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_WORX = SUPPORT_LANDROID_BASE

CONFIG_SCHEME = {
    vol.Optional(ATTR_RAINDELAY): vol.All(vol.Coerce(int), vol.Range(0, 300)),
    vol.Optional(ATTR_TIMEEXTENSION): vol.All(vol.Coerce(int), vol.Range(-100, 100)),
    vol.Optional(ATTR_MULTIZONE_DISTANCES): str,
    vol.Optional(ATTR_MULTIZONE_PROBABILITIES): str,
}

OTS_SCHEME = {
    vol.Required(ATTR_BOUNDARY, default=False): bool,
    vol.Required(ATTR_RUNTIME, default=30): vol.Coerce(int),
}

SUPPORTED_SERVICES = (
    SERVICE_CONFIG,
    SERVICE_PARTYMODE,
    SERVICE_SETZONE,
    SERVICE_LOCK,
    SERVICE_RESTART,
    SERVICE_EDGECUT,
    SERVICE_OTS,
)


class WorxButton(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Worx Landroid button."""


class WorxMowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Worx Landroid device."""

    # def __init__(self, hass, api):
    #     """Init new base device."""
    #     super().__init__(hass, api)
    #     device: WorxCloud = self.api.device

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_WORX

    async def async_toggle_lock(self, service_call: ServiceCall = None):
        """Toggle locked state."""
        device: WorxCloud = self.api.device
        set_lock = not bool(device.locked)
        _LOGGER.debug("Setting locked state for %s to %s", self._name, set_lock)
        await self.hass.async_add_executor_job(partial(device.lock, set_lock))

    async def async_toggle_partymode(self, service_call: ServiceCall = None):
        """Toggle partymode state."""
        device: WorxCloud = self.api.device
        set_partymode = not bool(device.partymode_enabled)
        _LOGGER.debug("Setting PartyMode to %s on %s", set_partymode, self._name)
        try:
            await self.hass.async_add_executor_job(
                partial(device.toggle_partymode, set_partymode)
            )
        except NoPartymodeError as ex:
            _LOGGER.error("(%s) %s", self._name, ex.args[0])

    async def async_edgecut(self, service_call: ServiceCall = None):
        """Start edgecut routine."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Starting edgecut routine for %s", self._name)
        try:
            await self.hass.async_add_executor_job(partial(device.ots, True, 0))
        except NoOneTimeScheduleError as ex:
            _LOGGER.error("(%s) %s", self._name, ex.args[0])

    async def async_restart(self, service_call: ServiceCall = None):
        """Restart mower baseboard OS."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Restarting %s", self._name)
        await self.hass.async_add_executor_job(device.restart)

    async def async_ots(self, service_call: ServiceCall):
        """Begin OTS routine."""
        device: WorxCloud = self.api.device
        data = service_call.data
        _LOGGER.debug(
            "Starting OTS on %s, doing boundary (%s) running for %s minutes",
            self._name,
            data["boundary"],
            data["runtime"],
        )
        await self.hass.async_add_executor_job(
            partial(device.ots, data["boundary"], data["runtime"])
        )

    async def async_config(self, service_call: ServiceCall):
        """Set config parameters."""
        tmpdata = {}
        device: WorxCloud = self.api.device
        data = service_call.data

        if "raindelay" in data:
            _LOGGER.debug(
                "Setting raindelay on %s to %s minutes", self._name, data["raindelay"]
            )
            tmpdata["rd"] = int(data["raindelay"])

        if "timeextension" in data:
            _LOGGER.debug(
                "Setting timeextension on %s to %s%%", self._name, data["timeextension"]
            )
            tmpdata["sc"] = {}
            tmpdata["sc"]["p"] = int(data["timeextension"])

        if "multizone_distances" in data:
            _LOGGER.debug(
                "Setting multizone distances on %s to %s",
                self._name,
                data["multizone_distances"],
            )
            sections = [
                int(x)
                for x in data["multizone_distances"]
                .replace("[", "")
                .replace("]", "")
                .split(",")
            ]
            if len(sections) != 4:
                raise HomeAssistantError(
                    "Incorrect format for multizone distances array"
                )

            tmpdata["mz"] = sections

        if "multizone_probabilities" in data:
            _LOGGER.debug(
                "Setting multizone probabilities on %s to %s",
                self._name,
                data["multizone_probabilities"],
            )
            tmpdata["mzv"] = []
            sections = [
                int(x)
                for x in data["multizone_probabilities"]
                .replace("[", "")
                .replace("]", "")
                .split(",")
            ]
            if len(sections) != 4:
                raise HomeAssistantError(
                    "Incorrect format for multizone probabilities array"
                )
            if sum(sections) != 100:
                raise HomeAssistantError("Sum of zone probabilities array MUST be 100")

            for idx, val in enumerate(sections):
                share = int(int(val) / 10)
                _LOGGER.debug("%s: %s (%s)", idx, val, share)
                for _ in range(share):
                    tmpdata["mzv"].append(idx)

        if tmpdata:
            data = json.dumps(tmpdata)
            _LOGGER.debug("%s got new config: %s", self._name, data)
            await self.hass.async_add_executor_job(partial(device.send, data))
