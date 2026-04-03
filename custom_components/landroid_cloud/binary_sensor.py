"""Binary sensor platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LandroidBaseEntity


@dataclass(frozen=True, kw_only=True)
class LandroidBinarySensorDescription(BinarySensorEntityDescription):
    """Description for Landroid binary sensors."""

    requires_online: bool = False


BINARY_SENSORS: tuple[LandroidBinarySensorDescription, ...] = (
    LandroidBinarySensorDescription(
        key="rain_sensor",
        translation_key="rain_sensor",
        device_class=BinarySensorDeviceClass.MOISTURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_category=EntityCategory.DIAGNOSTIC,
        requires_online=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidBinarySensor] = []

    for serial_number in coordinator.data:
        for description in BINARY_SENSORS:
            entities.append(
                LandroidBinarySensor(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidBinarySensor(LandroidBaseEntity, BinarySensorEntity):
    """Representation of a Landroid cloud binary sensor."""

    entity_description: LandroidBinarySensorDescription

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidBinarySensorDescription,
    ) -> None:
        """Initialize binary sensor entity."""
        self.entity_description = description
        self._attr_requires_online = description.requires_online
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if binary sensor is on."""
        key = self.entity_description.key
        if key == "rain_sensor":
            return bool(self.device.rainsensor.get("triggered", False))

        if key == "charging":
            charging = self.device.battery.get("charging")
            if isinstance(charging, bool):
                return charging
            return None

        return None
