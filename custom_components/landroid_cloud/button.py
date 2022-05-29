"""Representation of a button."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
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

    landroid_mower = constructor(hass, api)

    async_add_entities([landroid_mower], True)
