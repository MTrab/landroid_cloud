"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import LandroidCloudBase, WorxDevice, KressDevice, LandxcapeDevice

_LOGGER = logging.getLogger(__name__)


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
    elif vendor == "kress":
        constructor = KressDevice
    else:
        constructor = LandxcapeDevice

    landroid_mower = constructor(hass, api)
    async_add_entities([landroid_mower], True)
