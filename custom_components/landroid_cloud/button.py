"""Representation of a button."""
from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .devices.worx import WorxButton
from .devices.landxcape import LandxcapeButton
from .devices.kress import KressButton

from .device_base import LandroidCloudButtonBase

from .const import DOMAIN, LandroidButtonTypes

_LOGGER = logging.getLogger(__name__)

# Tuple containing buttons to create
BUTTONS = [
    ButtonEntityDescription(
        key=LandroidButtonTypes.RESTART,
        name="Restart",
        icon="mdi:restart",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=ButtonDeviceClass.RESTART,
    ),
    ButtonEntityDescription(
        key=LandroidButtonTypes.EDGECUT,
        name="Start cutting edge",
        icon="mdi:map-marker-path",
        entity_category=None,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
    entities: list[LandroidCloudButtonBase] = []
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]

        for landroidbutton in BUTTONS:
            constructor: type[LandroidCloudButtonBase]
            vendor = hass.data[DOMAIN][config.entry_id][CONF_TYPE].lower()
            if vendor == "worx":
                constructor = WorxButton
            elif vendor == "kress":
                constructor = KressButton
            else:
                constructor = LandxcapeButton

            entities.append(constructor(landroidbutton, hass, api))

    async_add_entities(entities, True)
