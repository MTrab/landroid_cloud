"""Representation of a button."""

from __future__ import annotations

import asyncio
from copy import deepcopy

from homeassistant.components.button import ButtonDeviceClass, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI
from .const import (
    ATTR_DEVICES,
    DOMAIN,
    LOGLEVEL,
    LandroidButtonTypes,
    LandroidFeatureSupport,
)
from .device_base import LandroidButton
from .utils.entity_setup import vendor_to_device
from .utils.logger import LandroidLogger, LoggerType

# Tuple containing buttons to create
BUTTONS = [
    ButtonEntityDescription(
        key=LandroidButtonTypes.RESTART,
        name="Restart",
        icon="mdi:restart",
        entity_category=EntityCategory.CONFIG,
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
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        logger = LandroidLogger(name=__name__, api=api, log_level=LOGLEVEL)

        for button in BUTTONS:
            if (
                button.key == LandroidButtonTypes.RESTART
                and api.features & LandroidFeatureSupport.RESTART
            ) or (
                button.key == LandroidButtonTypes.EDGECUT
                and api.features & LandroidFeatureSupport.EDGECUT
            ):
                logger.log(LoggerType.FEATURE, "Adding %s button", button.key)
                entity = LandroidButton(hass, button, api, config)

                entities.append(entity)

    async_add_entities(entities, True)
