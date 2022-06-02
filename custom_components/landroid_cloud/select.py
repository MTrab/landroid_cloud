"""Representation of a select entity."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .devices.worx import WorxSelect, WorxZoneSelect

# from .devices.landxcape import LandxcapeButton
# from .devices.kress import KressButton

from .device_base import SELECT, LandroidCloudSelectEntity

from .const import DOMAIN, LandroidSelectTypes


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
    api = hass.data[DOMAIN][config.entry_id]["api"]
    entities: list[LandroidCloudSelectEntity] = []

    for select in SELECT:
        constructor: type[LandroidCloudSelectEntity]
        vendor = api.data.get(CONF_TYPE).lower()
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
