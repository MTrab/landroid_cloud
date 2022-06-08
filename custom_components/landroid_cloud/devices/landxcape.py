"""LandXcape device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send

from pyworxcloud import (
    WorxCloud,
)

from .. import LandroidAPI

from ..const import ATTR_BOUNDARY, ATTR_MULTIZONE_DISTANCES, ATTR_MULTIZONE_PROBABILITIES, ATTR_RAINDELAY, ATTR_RUNTIME, ATTR_TIMEEXTENSION, UPDATE_SIGNAL_ZONES, LandroidFeatureSupport

from ..device_base import (
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    SUPPORT_LANDROID_BASE,
    LandroidCloudSelectEntity,
    LandroidCloudSelectZoneEntity,
)


_LOGGER = logging.getLogger(__name__)

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
    """Definition of Landxcape button."""

    def __init__(
        self,
        description: ButtonEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ) -> None:
        """Initialize a Landxcape button."""
        super().__init__(description, hass, api, DEVICE_FEATURES)
        _LOGGER.debug(
            "(%s) Adding %s",
            self.api.name,
            description.key,
        )
        self.device: WorxCloud = self.api.device


class Select(LandroidCloudSelectEntity):
    """Definition of Landxcape select entity."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ):
        """Init new Landxcape Select entity."""
        super().__init__(description, hass, api, DEVICE_FEATURES)
        self.device: WorxCloud = self.api.device


class ZoneSelect(Select, LandroidCloudSelectZoneEntity):
    """Definition of a Landxcape zone selector."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ):
        """Init new Landxcape Zone Select entity."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device


class MowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Landxcape device."""

    def __init__(self, hass: HomeAssistant, api: LandroidAPI):
        """Initialize a Landxcape mower device."""
        super().__init__(hass, api, DEVICE_FEATURES)

        self.register_services()

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES
    def zone_mapping(self) -> None:
        """Map current zone correct."""
        device: WorxCloud = self.api.device
        current_zone = device.mowing_zone
        virtual_zones = device.zone_probability
        _LOGGER.debug("(%s) Zone reported by API: %s", self.api.name, current_zone)
        _LOGGER.debug(
            "(%s) Corrected zone: %s", self.api.name, virtual_zones[current_zone]
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