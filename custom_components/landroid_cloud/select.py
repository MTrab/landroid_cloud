"""Input select for landroid_cloud."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidSelect, LandroidSelectEntityDescription

INPUT_SELECT = [
    LandroidSelectEntityDescription(
        key="zoneselect",
        name="Current zone",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        unit_of_measurement=None,
        options=["1", "2", "3", "4"],
        value_fn=lambda device: device.zone.current,
        command_fn=lambda api, value: api.cloud.setzone(
            api.device.serial_number, value
        ),
        icon="mdi:map-clock",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the switch platform."""
    entities = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        for select in INPUT_SELECT:
            entity = LandroidSelect(hass, select, api, config)
            entities.append(entity)

    async_add_devices(entities)
