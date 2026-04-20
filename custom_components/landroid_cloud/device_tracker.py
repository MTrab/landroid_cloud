"""Device tracker platform for Landroid Cloud."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LandroidBaseEntity, device_coordinates, device_supports_location


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud device tracker entities."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        LandroidCloudLocationEntity(coordinator, entry, serial_number)
        for serial_number, device in coordinator.data.items()
        if device_supports_location(device)
    )


class LandroidCloudLocationEntity(LandroidBaseEntity, TrackerEntity):
    """Representation of a mower GPS location."""

    _attr_source_type = SourceType.GPS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry, serial_number: str) -> None:
        """Initialize location tracker entity."""
        super().__init__(coordinator, config_entry, serial_number, "location")

    @property
    def name(self) -> str:
        """Return entity name."""
        return "Location"

    @property
    def available(self) -> bool:
        """Return availability for the tracker."""
        return super().available and device_coordinates(self.device) is not None

    @property
    def latitude(self) -> float | None:
        """Return current latitude."""
        if (coordinates := device_coordinates(self.device)) is None:
            return None

        return coordinates[0]

    @property
    def longitude(self) -> float | None:
        """Return current longitude."""
        if (coordinates := device_coordinates(self.device)) is None:
            return None

        return coordinates[1]
