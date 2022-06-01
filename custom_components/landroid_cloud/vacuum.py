"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations

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
    SERVICE_OTS,
    SERVICE_PARTYMODE,
    SERVICE_RESTART,
    SERVICE_SCHEDULE,
    SERVICE_SETZONE,
)
from .device_base import LandroidCloudBase
from .devices.worx import (
    WorxDevice,
    CONFIG_SCHEME as WORX_CONFIG,
    OTS_SCHEME as WORX_OTS,
)
from .devices.kress import KressDevice
from .devices.landxcape import LandxcapeDevice
from .scheme import SCHEDULE_SCHEME as SCHEME_SCHEDULE


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iRobot Roomba vacuum cleaner."""
    api = hass.data[DOMAIN][config.entry_id]["api"]

    platform = entity_platform.async_get_current_platform()
    constructor: type[LandroidCloudBase]
    vendor = api.data.get(CONF_TYPE).lower()

    if vendor == "worx":
        constructor = WorxDevice
        # Register custom services
        platform.async_register_entity_service(
            SERVICE_EDGECUT,
            {},
            constructor.async_edgecut,
        )
        platform.async_register_entity_service(
            SERVICE_LOCK,
            {},
            constructor.async_toggle_lock,
        )
        platform.async_register_entity_service(
            SERVICE_PARTYMODE,
            {},
            constructor.async_toggle_partymode,
        )
        platform.async_register_entity_service(
            SERVICE_SETZONE,
            {vol.Required(ATTR_ZONE): vol.All(vol.Coerce(int), vol.Range(0, 3))},
            constructor.async_setzone,
        )
        platform.async_register_entity_service(
            SERVICE_RESTART,
            {},
            constructor.async_restart,
        )
        platform.async_register_entity_service(
            SERVICE_CONFIG,
            WORX_CONFIG,
            constructor.async_config,
        )
        platform.async_register_entity_service(
            SERVICE_OTS,
            WORX_OTS,
            constructor.async_ots,
        )
    elif vendor == "kress":
        constructor = KressDevice
    else:
        constructor = LandxcapeDevice

    platform.async_register_entity_service(
        SERVICE_SCHEDULE,
        SCHEME_SCHEDULE,
        constructor.async_set_schedule,
    )

    landroid_mower = constructor(hass, api)

    async_add_entities([landroid_mower], True)
