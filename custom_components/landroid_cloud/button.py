"""Representation of a button."""
from __future__ import annotations
import asyncio
from copy import deepcopy

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI

from .const import (
    DOMAIN,
    LOGLEVEL,
    LandroidButtonTypes,
    LandroidFeatureSupport,
)
from .utils.entity_setup import vendor_to_device
from .utils.logger import LandroidLogger, LoggerType

LOGGER = LandroidLogger(__name__, LOGLEVEL)

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
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api: LandroidAPI = hass.data[DOMAIN][config.entry_id][idx]["api"]
        vendor = api.config["type"]
        device = vendor_to_device(vendor)

        while not api.features_loaded:
            await asyncio.sleep(1)

        LOGGER.set_api(api)

        LOGGER.write(LoggerType.FEATURE_ASSESSMENT, "Assessing available buttons")
        for button in BUTTONS:
            constructor = None
            if (
                button.key == LandroidButtonTypes.RESTART
                and api.features & LandroidFeatureSupport.RESTART
            ) or (
                button.key == LandroidButtonTypes.EDGECUT
                and api.features & LandroidFeatureSupport.EDGECUT
            ):
                LOGGER.write(LoggerType.FEATURE, "Adding %s button", button.key)
                out = deepcopy(button)
                out.name = out.name.replace("NAME", api.friendly_name)
                constructor = device.Button

            if not isinstance(constructor, type(None)):
                entities.append(constructor(out, hass, api))

    async_add_entities(entities, True)
