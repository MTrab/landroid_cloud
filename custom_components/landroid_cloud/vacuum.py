"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations
from datetime import timedelta
from functools import partial

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ZONE,
    DOMAIN,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_PARTYMODE,
    SERVICE_RESTART,
    SERVICE_SETZONE,
)
from .device_base import LandroidCloudBase
from .devices.worx import WorxDevice, CONFIG_SCHEME as WORX_CONFIG
from .devices.kress import KressDevice
from .devices.landxcape import LandxcapeDevice

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=20)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iRobot Roomba vacuum cleaner."""
    api = hass.data[DOMAIN][config.entry_id]["api"]

    constructor: type[LandroidCloudBase]
    vendor = api.data.get(CONF_TYPE).lower()
    if vendor == "worx":
        constructor = WorxDevice
        # Register custom services
        platform = entity_platform.async_get_current_platform()

        platform.async_register_entity_service(
            SERVICE_EDGECUT,
            {},
            constructor.async_edgecut.__name__,
        )
        platform.async_register_entity_service(
            SERVICE_LOCK,
            {},
            constructor.async_toggle_lock.__name__,
        )
        platform.async_register_entity_service(
            SERVICE_PARTYMODE,
            {},
            constructor.async_toggle_partymode.__name__,
        )
        platform.async_register_entity_service(
            SERVICE_SETZONE,
            {vol.Required(ATTR_ZONE): vol.All(vol.Coerce(int), vol.Range(0, 3))},
            constructor.async_setzone,
        )
        platform.async_register_entity_service(
            SERVICE_RESTART,
            {},
            constructor.async_restart.__name__,
        )
        platform.async_register_entity_service(
            SERVICE_CONFIG,
            WORX_CONFIG,
            partial(constructor.async_config),
        )
    elif vendor == "kress":
        constructor = KressDevice
    else:
        constructor = LandxcapeDevice

    landroid_mower = constructor(hass, api)

    async_add_entities([landroid_mower], True)
