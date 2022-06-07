"""Representation of a button."""
from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LandroidButtonTypes,
    LandroidFeatureSupport,
)
from .utils.entity_setup import vendor_to_device

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
    entities = []
    _LOGGER.info("Assessing available buttons")
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]
        vendor = api.config["type"]
        device = vendor_to_device(vendor)

        for button in BUTTONS:
            constructor = None
            if (
                button.key == LandroidButtonTypes.RESTART
                and device.DEVICE_FEATURES & LandroidFeatureSupport.RESTART
            ) or (
                button.key == LandroidButtonTypes.EDGECUT
                and device.DEVICE_FEATURES & LandroidFeatureSupport.EDGECUT
            ):
                constructor = device.Button

            if not isinstance(constructor, type(None)):
                entities.append(constructor(button, hass, api))

    async_add_entities(entities, True)
