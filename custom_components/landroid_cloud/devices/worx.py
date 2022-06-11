"""Worx Landroid device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations
import json

from functools import partial
import voluptuous as vol

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity

from pyworxcloud import (
    WorxCloud,
)

from ..api import LandroidAPI

from ..const import (
    ATTR_BOUNDARY,
    ATTR_MULTIZONE_DISTANCES,
    ATTR_MULTIZONE_PROBABILITIES,
    ATTR_RAINDELAY,
    ATTR_RUNTIME,
    ATTR_TIMEEXTENSION,
    ATTR_TORQUE,
    LOGLEVEL,
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

from ..utils.logger import LandroidLogger, LoggerType

LOGGER = LandroidLogger(__name__, LOGLEVEL)

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
    | LandroidFeatureSupport.LOCK
    | LandroidFeatureSupport.CONFIG
    | LandroidFeatureSupport.RESTART
    | LandroidFeatureSupport.SELECT
    | LandroidFeatureSupport.SETZONE
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
        LOGGER.write(
            LoggerType.BUTTON,
            "Adding %s",
            description.key,
        )
        self.device: WorxCloud = self.api.device


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
        LOGGER.write(
            LoggerType.SELECT,
            "Adding %s",
            description.key,
        )
        self.device: WorxCloud = self.api.device


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

        self.register_services()

    @property
    def base_features(self):
        """Flag which Landroid Cloud specific features that are supported."""
        return DEVICE_FEATURES

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES

    def zone_mapping(self) -> None:
        """Map current zone correct."""
        device: WorxCloud = self.api.device
        current_zone = device.mowing_zone
        virtual_zones = device.zone_probability
        LOGGER.write(LoggerType.MOWER, "Zone reported by API: %s", current_zone)
        LOGGER.write(
            LoggerType.MOWER, "Corrected zone: %s", virtual_zones[current_zone]
        )
        self._attributes.update({"current_zone": virtual_zones[current_zone]})
        self.api.shared_options.update({"current_zone": virtual_zones[current_zone]})
        dispatcher_send(self.hass, f"{UPDATE_SIGNAL_ZONES}_{device.name}")

    @staticmethod
    def get_ots_scheme():
        """Get device specific OTS_SCHEME."""
        return OTS_SCHEME

    @staticmethod
    def get_config_scheme():
        """Get device specific CONFIG_SCHEME."""
        return CONFIG_SCHEME

    async def async_set_torque(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set wheel torque."""
        device: WorxCloud = self.api.device
        data = service_call.data
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Setting wheel torque to %s",
            data[ATTR_TORQUE],
        )
        tmpdata = {"cfg": {"tq": data[ATTR_TORQUE]}}
        await self.hass.async_add_executor_job(
            partial(device.send, json.dumps(tmpdata))
        )
