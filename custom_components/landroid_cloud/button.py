"""Representation of a button."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .devices.worx import WorxButton
from .devices.landxcape import LandxcapeButton
from .devices.kress import KressButton

from .device_base import BUTTONS, LandroidCloudButtonBase

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
    api = hass.data[DOMAIN][config.entry_id]["api"]
    entities: list[LandroidCloudButtonBase] = []

    for button in BUTTONS:
        constructor: type[LandroidCloudButtonBase]
        vendor = api.data.get(CONF_TYPE).lower()
        if vendor == "worx":
            constructor = WorxButton
        elif vendor == "kress":
            constructor = KressButton
        else:
            constructor = LandxcapeButton

        entities.append(constructor(button, hass, api))

    async_add_entities(entities, True)
