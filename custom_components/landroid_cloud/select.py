"""Select platform for Landroid Cloud."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        LandroidZoneSelect(
            coordinator=coordinator,
            config_entry=entry,
            serial_number=serial_number,
        )
        for serial_number in coordinator.data
    )


class LandroidZoneSelect(LandroidBaseEntity, SelectEntity):
    """Representation of zone selection."""

    _attr_icon = "mdi:map-clock"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "zone"

    def __init__(self, coordinator, config_entry, serial_number: str) -> None:
        """Initialize select entity."""
        super().__init__(coordinator, config_entry, serial_number, "zone")

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Disable zone select by default."""
        return False

    @property
    def options(self) -> list[str]:
        """Return available zone options."""
        starting_points = self.device.zone.get("starting_point", [])
        zone_count = len(starting_points)
        if zone_count == 0:
            zone_count = 4
        return [str(zone) for zone in range(1, zone_count + 1)]

    @property
    def current_option(self) -> str | None:
        """Return current selected zone."""
        index = self.device.zone.get("index", 0)
        return str(int(index) + 1)

    async def async_select_option(self, option: str) -> None:
        """Set selected zone."""
        zone = int(option)
        serial_number = str(self.device.serial_number)
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.setzone(serial_number, zone)
        )
