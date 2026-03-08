"""Sensor platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_BATTERY_CHARGING,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LandroidBaseEntity


@dataclass(frozen=True, kw_only=True)
class LandroidSensorDescription(SensorEntityDescription):
    """Description for Landroid sensors."""


def _battery_charging_attribute(device) -> dict[str, bool] | None:
    """Return Home Assistant battery charging attribute when available."""
    charging = getattr(device, "battery", {}).get("charging")
    if isinstance(charging, bool):
        return {ATTR_BATTERY_CHARGING: charging}
    return None


SENSORS: tuple[LandroidSensorDescription, ...] = (
    LandroidSensorDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LandroidSensorDescription(
        key="status",
        translation_key="status",
    ),
    LandroidSensorDescription(
        key="error",
        translation_key="error",
    ),
    LandroidSensorDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="daily_progress",
        translation_key="daily_progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="next_schedule",
        translation_key="next_schedule",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud sensor entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidSensor] = []

    for serial_number in coordinator.data:
        for description in SENSORS:
            entities.append(
                LandroidSensor(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidSensor(LandroidBaseEntity, SensorEntity):
    """Representation of a Landroid cloud sensor."""

    entity_description: LandroidSensorDescription

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidSensorDescription,
    ) -> None:
        """Initialize sensor entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def native_value(self):
        """Return the native value for this sensor."""
        device = self.device
        key = self.entity_description.key

        if key == "battery":
            return device.battery.get("percent")
        if key == "status":
            return device.status.get("description")
        if key == "error":
            return device.error.get("description")
        if key == "rssi":
            return device.get("rssi")
        if key == "daily_progress":
            return device.schedules.get("daily_progress")
        if key == "next_schedule":
            return device.schedules.get("next_schedule_start")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, bool] | None:
        """Return battery charging attribute for battery sensor."""
        if self.entity_description.key != "battery":
            return None
        return _battery_charging_attribute(self.device)
