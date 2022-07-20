"""Worx Landroid device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import json
from functools import partial

import voluptuous as vol
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import HomeAssistant
from pyworxcloud import WorxCloud

from ..api import LandroidAPI
from ..const import (
    ATTR_BOUNDARY,
    ATTR_MULTIZONE_DISTANCES,
    ATTR_MULTIZONE_PROBABILITIES,
    ATTR_RAINDELAY,
    ATTR_RUNTIME,
    ATTR_TIMEEXTENSION,
    ATTR_TORQUE,
    LandroidFeatureSupport,
)
from ..device_base import (
    SUPPORT_LANDROID_BASE,
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    LandroidCloudSelectEntity,
    LandroidCloudSelectZoneEntity,
)
from ..utils.logger import LoggerType

# from homeassistant.helpers.dispatcher import dispatcher_send


SUPPORTED_FEATURES = SUPPORT_LANDROID_BASE

CONFIG_SCHEME = vol.Schema(
    {
        vol.Optional(ATTR_RAINDELAY): vol.All(vol.Coerce(int), vol.Range(0, 300)),
        vol.Optional(ATTR_TIMEEXTENSION): vol.All(
            vol.Coerce(int), vol.Range(-100, 100)
        ),
        vol.Optional(ATTR_MULTIZONE_DISTANCES): str,
        vol.Optional(ATTR_MULTIZONE_PROBABILITIES): str,
    }
)

OTS_SCHEME = vol.Schema(
    {
        vol.Required(ATTR_BOUNDARY, default=False): bool,
        vol.Required(ATTR_RUNTIME, default=30): vol.Coerce(int),
    }
)

DEVICE_FEATURES = (
    LandroidFeatureSupport.MOWER
    | LandroidFeatureSupport.BUTTON
    | LandroidFeatureSupport.SELECT
    | LandroidFeatureSupport.LOCK
    | LandroidFeatureSupport.CONFIG
    | LandroidFeatureSupport.RESTART
    | LandroidFeatureSupport.REFRESH
    | LandroidFeatureSupport.SETZONE
    | LandroidFeatureSupport.RAW
    | LandroidFeatureSupport.SCHEDULES
)


class Button(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Worx Landroid button."""

    def __init__(
        self,
        description: ButtonEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ) -> None:
        """Initialize a button."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device
        self.log(
            LoggerType.SELECT,
            "Adding %s",
            description.key,
        )


class Select(LandroidCloudSelectEntity):
    """Definition of Worx Landroid select entity."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ):
        """Init new Worx Select entity."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device
        self.log(
            LoggerType.SELECT,
            "Adding %s",
            description.key,
        )


class ZoneSelect(Select, LandroidCloudSelectZoneEntity):
    """Definition of a Worx zone selector."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ):
        """Init new Worx Zone Select entity."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device


class MowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Worx Landroid device."""

    def __init__(self, hass, api):
        """Initialize mower entity."""
        super().__init__(hass, api)
        self.device: WorxCloud = self.api.device

    @property
    def base_features(self):
        """Flag which Landroid Cloud specific features that are supported."""
        return DEVICE_FEATURES

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

    async def async_set_torque(self, data: dict | None = None) -> None:
        """Set wheel torque."""
        device: WorxCloud = self.api.device
        self.log(
            LoggerType.SERVICE_CALL,
            "Setting wheel torque to %s",
            data[ATTR_TORQUE],
        )
        tmpdata = {"tq": data[ATTR_TORQUE]}
        await self.hass.async_add_executor_job(
            partial(device.send, json.dumps(tmpdata))
        )
