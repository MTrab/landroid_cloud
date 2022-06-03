"""Representation of a button."""
from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LandroidButtonTypes, LandroidFeatureSupport
from .utils.entity_setup import async_register_services, vendor_to_device

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
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]

        platform = entity_platform.async_get_current_platform()
        for button in BUTTONS:
            vendor = api.config["type"]
            device = vendor_to_device(vendor)
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
                await async_register_services(
                    api, platform, constructor, device, constructor.features
                )

    async_add_entities(entities, True)
