"""Representation of a select entity."""
from __future__ import annotations

import asyncio
from copy import deepcopy

from homeassistant.components.select import SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI
from .const import (
    ATTR_DEVICES,
    DOMAIN,
    LOGLEVEL,
    LandroidFeatureSupport,
    LandroidSelectTypes,
)
from .utils.entity_setup import vendor_to_device
from .utils.logger import LandroidLogger, LoggerType

# Tuple containing select entities to create
SELECTS = [
    SelectEntityDescription(
        key=LandroidSelectTypes.NEXT_ZONE,
        name="NAME - Select Next Zone",
        icon="mdi:map-clock",
        entity_category=EntityCategory.CONFIG,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
    entities = []
    for name, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        device = vendor_to_device(api.config["type"])

        await api.async_await_features()

        logger = LandroidLogger(name=__name__, api=api, log_level=LOGLEVEL)
        logger.log(
            LoggerType.FEATURE_ASSESSMENT,
            "Features fully loaded, feature bit: %s -- assessing available select entities",
            api.features,
        )
        for select in SELECTS:
            constructor = None
            if (
                select.key == LandroidSelectTypes.NEXT_ZONE
                and device.DEVICE_FEATURES & LandroidFeatureSupport.SETZONE
            ):
                logger.log(LoggerType.FEATURE, "Adding %s select", select.key)

                out = deepcopy(select)
                out.name = out.name.replace("NAME", api.friendly_name)
                constructor = device.ZoneSelect

            if not isinstance(constructor, type(None)):
                entities.append(constructor(out, hass, api))

    async_add_entities(entities, True)
