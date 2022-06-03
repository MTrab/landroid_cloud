"""Representation of a select entity."""
from __future__ import annotations

from homeassistant.components.select import (
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LandroidFeatureSupport, LandroidSelectTypes
from .utils.entity_setup import async_register_services, vendor_to_device

# Tuple containing select entities to create
SELECTS = [
    SelectEntityDescription(
        key=LandroidSelectTypes.NEXT_ZONE,
        name="Select Next Zone",
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
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]

        platform = entity_platform.async_get_current_platform()
        for select in SELECTS:
            vendor = api.config["type"]
            device = vendor_to_device(vendor)
            constructor = None
            if (
                select.key == LandroidSelectTypes.NEXT_ZONE
                and device.DEVICE_FEATURES & LandroidFeatureSupport.SETZONE
            ):
                constructor = device.ZoneSelect

            if not isinstance(constructor, type(None)):
                entities.append(constructor(select, hass, api))
                await async_register_services(
                    api, platform, constructor, device, constructor.features
                )

    async_add_entities(entities, True)
