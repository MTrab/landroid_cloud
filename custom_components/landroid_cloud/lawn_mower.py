"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .utils.entity_setup import vendor_to_device


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the mower device."""
    mowers = []
    for name, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        device = vendor_to_device(api.config["type"])
        constructor = device.MowerDevice(hass, api)

        mowers.append(constructor)

    async_add_entities(mowers, True)
