"""Representation of a button."""
from __future__ import annotations
import asyncio
from copy import deepcopy

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LandroidAPI

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
        name="NAME - Restart",
        icon="mdi:restart",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=ButtonDeviceClass.RESTART,
    ),
    ButtonEntityDescription(
        key=LandroidButtonTypes.EDGECUT,
        name="NAME - Start cutting edge",
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
    _LOGGER.debug("Assessing available buttons")
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api: LandroidAPI = hass.data[DOMAIN][config.entry_id][idx]["api"]
        vendor = api.config["type"]
        device = vendor_to_device(vendor)

        while not api.features_loaded:
            await asyncio.sleep(1)

        _LOGGER.debug("Restart %s",api.features & LandroidFeatureSupport.RESTART)
        _LOGGER.debug("Edge cut %s",api.features & LandroidFeatureSupport.EDGECUT)
        for button in BUTTONS:
            constructor = None
            if (
                button.key == LandroidButtonTypes.RESTART
                and api.features & LandroidFeatureSupport.RESTART
            ) or (
                button.key == LandroidButtonTypes.EDGECUT
                and api.features & LandroidFeatureSupport.EDGECUT
            ):
                out = deepcopy(button)
                out.name = out.name.replace("NAME", api.friendly_name)
                constructor = device.Button

            if not isinstance(constructor, type(None)):
                entities.append(constructor(out, hass, api))

    async_add_entities(entities, True)
