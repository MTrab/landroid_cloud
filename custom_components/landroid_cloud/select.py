"""Representation of a select entity."""
from __future__ import annotations

from homeassistant.components.select import (
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .devices.worx import WorxSelect, WorxZoneSelect

# from .devices.landxcape import LandxcapeButton
# from .devices.kress import KressButton

from .device_base import LandroidCloudSelectEntity

from .const import DOMAIN, LandroidSelectTypes

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
    entities: list[LandroidCloudSelectEntity] = []
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api = hass.data[DOMAIN][config.entry_id][idx]["api"]

        for select in SELECTS:
            constructor: type[LandroidCloudSelectEntity]
            vendor = hass.data[DOMAIN][config.entry_id][CONF_TYPE].lower()
            if vendor == "worx":
                if select.key == LandroidSelectTypes.NEXT_ZONE:
                    constructor = WorxZoneSelect
                else:
                    constructor = WorxSelect
            # elif vendor == "kress":
            #     constructor = KressButton
            # else:
            #     constructor = LandxcapeButton

            entities.append(constructor(select, hass, api))

    async_add_entities(entities, True)
