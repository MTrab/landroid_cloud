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
    UnitOfLength,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
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


def _rain_delay_remaining_value(device) -> int | None:
    """Return remaining rain delay in minutes when available."""
    remaining = getattr(device, "rainsensor", {}).get("remaining")
    if isinstance(remaining, int):
        return remaining
    return None


def _battery_cycle_value(device, cycle_key: str) -> int | None:
    """Return battery cycle information when available."""
    cycles = getattr(device, "battery", {}).get("cycles", {})
    value = cycles.get(cycle_key)
    if isinstance(value, int):
        return value
    return None


def _battery_value(device, battery_key: str) -> float | None:
    """Return battery telemetry value when available."""
    value = getattr(device, "battery", {}).get(battery_key)
    if isinstance(value, int | float):
        return float(value)
    return None


def _blade_runtime_value(device, runtime_key: str) -> int | None:
    """Return blade runtime information in minutes when available."""
    value = getattr(device, "blades", {}).get(runtime_key)
    if isinstance(value, int):
        return value
    return None


def _statistics_value(device, statistics_key: str) -> int | None:
    """Return device statistics value when available."""
    value = getattr(device, "statistics", {}).get(statistics_key)
    if isinstance(value, int):
        return value
    return None


def _schedule_attributes(device) -> dict[str, object] | None:
    """Return known schedule fields for the next schedule sensor."""
    schedules = getattr(device, "schedules", None)
    if not isinstance(schedules, dict):
        return None

    known_keys = (
        "active",
        "time_extension",
        "slots",
        "party_mode_enabled",
        "one_time_schedule",
        "auto_schedule",
        "daily_progress",
        "next_schedule_start",
    )
    attributes = {
        key: schedules[key] for key in known_keys if key in schedules and schedules[key] is not None
    }
    return attributes or None


SENSORS: tuple[LandroidSensorDescription, ...] = (
    LandroidSensorDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LandroidSensorDescription(
        key="error",
        translation_key="error",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
    ),
    LandroidSensorDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="daily_progress",
        translation_key="daily_progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        icon="mdi:progress-clock",
    ),
    LandroidSensorDescription(
        key="next_schedule",
        translation_key="next_schedule",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="rain_delay_remaining",
        translation_key="rain_delay_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LandroidSensorDescription(
        key="battery_charge_cycles_total",
        translation_key="battery_charge_cycles_total",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:battery-sync",
    ),
    LandroidSensorDescription(
        key="battery_charge_cycles_current",
        translation_key="battery_charge_cycles_current",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:battery-sync",
    ),
    LandroidSensorDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="blade_runtime_total",
        translation_key="blade_runtime_total",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="blade_runtime_current",
        translation_key="blade_runtime_current",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="distance_driven_total",
        translation_key="distance_driven_total",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="mower_runtime_total",
        translation_key="mower_runtime_total",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
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
        if key == "error":
            return device.error.get("description")
        if key == "rssi":
            return getattr(device, "rssi", None)
        if key == "daily_progress":
            return device.schedules.get("daily_progress")
        if key == "next_schedule":
            return device.schedules.get("next_schedule_start")
        if key == "rain_delay_remaining":
            return _rain_delay_remaining_value(device)
        if key == "battery_charge_cycles_total":
            return _battery_cycle_value(device, "total")
        if key == "battery_charge_cycles_current":
            return _battery_cycle_value(device, "current")
        if key == "battery_temperature":
            return _battery_value(device, "temperature")
        if key == "battery_voltage":
            return _battery_value(device, "voltage")
        if key == "blade_runtime_total":
            return _blade_runtime_value(device, "total_on")
        if key == "blade_runtime_current":
            return _blade_runtime_value(device, "current_on")
        if key == "distance_driven_total":
            return _statistics_value(device, "distance")
        if key == "mower_runtime_total":
            return _statistics_value(device, "worktime_total")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return extra state attributes for sensors that expose them."""
        if self.entity_description.key == "battery":
            return _battery_charging_attribute(self.device)
        if self.entity_description.key == "next_schedule":
            return _schedule_attributes(self.device)
        return None
