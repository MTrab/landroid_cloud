"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .utils.entity_setup import vendor_to_device

_LOGGER = logging.getLogger(__name__)


def check_state():
    """Check state."""


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the mower device."""
    mowers = []
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]
        device = vendor_to_device(api.config["type"])
        constructor = device.MowerDevice

        mowers.append(constructor(hass, api))

    async_add_entities(mowers, True)
