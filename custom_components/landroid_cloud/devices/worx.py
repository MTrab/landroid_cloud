"""Worx Landroid device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations
import json

import logging

from functools import partial
import voluptuous as vol

from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import dispatcher_send

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
    UPDATE_SIGNAL_ZONES,
    LandroidFeatureSupport,
)

from ..device_base import (
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    SUPPORT_LANDROID_BASE,
    LandroidCloudSelectEntity,
    LandroidCloudSelectZoneEntity,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = SUPPORT_LANDROID_BASE

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

DEVICE_FEATURES = (
    LandroidFeatureSupport.MOWER
    | LandroidFeatureSupport.BUTTON
    | LandroidFeatureSupport.SELECT
    | LandroidFeatureSupport.SETZONE
    | LandroidFeatureSupport.LOCK
    | LandroidFeatureSupport.CONFIG
    | LandroidFeatureSupport.RESTART
    | LandroidFeatureSupport.SELECT
    | LandroidFeatureSupport.SETZONE
)


class Button(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Worx Landroid button."""

    def __init__(self, description, hass, api) -> None:
        """Initialize a button."""
        super().__init__(description, hass, api)
        _LOGGER.debug("Adding %s for %s", description.key, self.api.name)
        self.device: WorxCloud = self.api.device
        self._attr_landroid_features = DEVICE_FEATURES

        if api.device.partymode_capable:
            _LOGGER.debug("Device %s is party mode capable", self.api.name)
            self._attr_landroid_features = (
                self._attr_landroid_features | LandroidFeatureSupport.PARTYMODE
            )

        if api.device.ots_capable:
            _LOGGER.debug("Device %s is OTS capable", self.api.name)
            self._attr_landroid_features = (
                self._attr_landroid_features | LandroidFeatureSupport.EDGECUT
            )


class Select(LandroidCloudSelectEntity):
    """Definition of Worx Landroid button."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass,
        api,
    ):
        """Init new Worx Select entity."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device
        self._attr_landroid_features = DEVICE_FEATURES


class ZoneSelect(Select, LandroidCloudSelectZoneEntity):
    """Definition of a zone selector."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass,
        api,
    ):
        """Init new Worx Zone Select entity."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device
        self._attr_landroid_features = DEVICE_FEATURES



class MowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Worx Landroid device."""

    def __init__(self, hass, api):
        """Initialize mower entity."""
        super().__init__(hass, api)
        self._attr_landroid_features = DEVICE_FEATURES

        if api.device.partymode_capable:
            _LOGGER.debug("Device %s is party mode capable", self.api.name)
            self._attr_landroid_features = (
                self._attr_landroid_features | LandroidFeatureSupport.PARTYMODE
            )

        if api.device.ots_capable:
            _LOGGER.debug("Device %s is OTS capable", self.api.name)
            self._attr_landroid_features = (
                self._attr_landroid_features | LandroidFeatureSupport.EDGECUT
            )

        self.register_services()

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES

    @staticmethod
    def get_ots_scheme():
        """Get device specific OTS_SCHEME."""
        return OTS_SCHEME

    @staticmethod
    def get_config_scheme():
        """Get device specific CONFIG_SCHEME."""
        return CONFIG_SCHEME

    def zone_mapping(self) -> None:
        """Map current zone correct."""
        device: WorxCloud = self.api.device
        current_zone = device.mowing_zone
        virtual_zones = device.zone_probability
        _LOGGER.debug("Zone reported by API: %s", current_zone)
        _LOGGER.debug("Corrected zone: %s", virtual_zones[current_zone])
        self._attributes.update({"current_zone": virtual_zones[current_zone]})
        self.api.shared_options.update({"current_zone": virtual_zones[current_zone]})
        dispatcher_send(self.hass, f"{UPDATE_SIGNAL_ZONES}_{self.api.device.name}")

    async def async_toggle_lock(self, _: ServiceCall = None):
        """Toggle locked state."""
        device: WorxCloud = self.api.device
        set_lock = not bool(device.locked)
        _LOGGER.debug("Setting locked state for %s to %s", self._name, set_lock)
        await self.hass.async_add_executor_job(partial(device.lock, set_lock))

    async def async_toggle_partymode(self, _: ServiceCall = None):
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

    async def async_edgecut(self, _: ServiceCall = None):
        """Start edgecut routine."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Starting edgecut routine for %s", self._name)
        try:
            await self.hass.async_add_executor_job(partial(device.ots, True, 0))
        except NoOneTimeScheduleError as ex:
            _LOGGER.error("(%s) %s", self._name, ex.args[0])

    async def async_restart(self, _: ServiceCall = None):
        """Restart mower baseboard OS."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Restarting %s", self._name)
        await self.hass.async_add_executor_job(device.restart)

    async def async_ots(self, service_call: ServiceCall) -> None:
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

    async def async_config(self, service_call: ServiceCall) -> None:
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
            if not sum(sections) in [100, 0]:
                raise HomeAssistantError(
                    "Sum of zone probabilities array MUST be 100"
                    f"or 0 (disabled), request was: {sum(sections)}"
                )

            if sum(sections) == 0:
                for _ in range(10):
                    tmpdata["mzv"].append(0)
            else:
                for idx, val in enumerate(sections):
                    share = int(int(val) / 10)
                    for _ in range(share):
                        tmpdata["mzv"].append(idx)

        if tmpdata:
            data = json.dumps(tmpdata)
            _LOGGER.debug("%s got new config: %s", self._name, data)
            await self.hass.async_add_executor_job(partial(device.send, data))
