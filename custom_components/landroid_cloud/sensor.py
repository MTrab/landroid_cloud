"""Sensor platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_BATTERY_CHARGING,
    DEGREE,
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
from pyworxcloud.day_map import DAY_MAP

from .const import ERROR_STATE_MAP, ERROR_STATE_OPTIONS
from .entity import (
    LandroidBaseEntity,
    auto_schedule,
    auto_schedule_settings,
)


@dataclass(frozen=True, kw_only=True)
class LandroidSensorDescription(SensorEntityDescription):
    """Description for Landroid sensors."""

    requires_auto_schedule: bool = False


def _battery_charging_attribute(device) -> dict[str, bool] | None:
    """Return Home Assistant battery charging attribute when available."""
    charging = getattr(device, "battery", {}).get("charging")
    if isinstance(charging, bool):
        return {ATTR_BATTERY_CHARGING: charging}
    return None


def _rain_delay_remaining_value(device) -> int | None:
    """Return remaining rain delay in minutes when available."""
    remaining = getattr(device, "rainsensor", {}).get("remaining")
    if isinstance(remaining, int) and remaining > 0:
        return remaining
    return None


def _daily_progress_value(device) -> int | None:
    """Return daily progress percentage when available."""
    progress = getattr(device, "schedules", {}).get("daily_progress")
    if isinstance(progress, int):
        return progress
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


def _orientation_value(device, orientation_key: str) -> float | None:
    """Return one orientation axis in degrees when available."""
    value = getattr(device, "orientation", {}).get(orientation_key)
    if isinstance(value, int | float):
        return float(value)
    return None


def _blade_runtime_value(device, runtime_key: str) -> int | None:
    """Return blade runtime information in minutes when available."""
    value = getattr(device, "blades", {}).get(runtime_key)
    if isinstance(value, int):
        return value
    return None


def _blade_reset_time_value(device) -> datetime | None:
    """Return blade reset timestamp when available."""
    value = getattr(device, "blades", {}).get("reset_time")
    if isinstance(value, datetime):
        return value
    return None


def _last_update_value(device) -> datetime | None:
    """Return last update timestamp in UTC when available."""
    value = getattr(device, "updated", None)
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    return None


def _statistics_value(device, statistics_key: str) -> int | None:
    """Return device statistics value when available."""
    value = getattr(device, "statistics", {}).get(statistics_key)
    if isinstance(value, int):
        return value
    return None


def _schedule_attributes(device) -> dict[str, object] | None:
    """Return known schedule fields for the next schedule sensor."""
    return _schedule_attributes_with_normalized_schedule(device, None)


def _nutrition_value(device) -> str | None:
    """Return nutrition as an N/P/K string when configured."""
    nutrition = auto_schedule_settings(device).get("nutrition")
    if not isinstance(nutrition, dict):
        return None

    n = nutrition.get("n")
    p = nutrition.get("p")
    k = nutrition.get("k")
    if not all(isinstance(value, int) for value in (n, p, k)):
        return None

    return f"N:{n} P:{p} K:{k}"


def _nutrition_attributes(device) -> dict[str, int] | None:
    """Return nutrition values as attributes when configured."""
    nutrition = auto_schedule_settings(device).get("nutrition")
    if not isinstance(nutrition, dict):
        return None
    if not all(isinstance(nutrition.get(key), int) for key in ("n", "p", "k")):
        return None
    return {key: int(nutrition[key]) for key in ("n", "p", "k")}


def _exclusion_schedule_value(device) -> int:
    """Return a compact count of configured exclusion rules."""
    exclusion = auto_schedule_settings(device).get("exclusion_scheduler")
    if not isinstance(exclusion, dict):
        return 0

    total = 0
    for day in exclusion.get("days", []):
        if not isinstance(day, dict):
            continue
        if day.get("exclude_day"):
            total += 1
        slots = day.get("slots", [])
        if isinstance(slots, list):
            total += len([slot for slot in slots if isinstance(slot, dict)])
    return total


def _exclusion_schedule_attributes(device) -> dict[str, object] | None:
    """Return structured exclusion-scheduler data."""
    exclusion = auto_schedule_settings(device).get("exclusion_scheduler")
    if not isinstance(exclusion, dict):
        return None

    days: list[dict[str, object]] = []
    for index, raw_day in enumerate(exclusion.get("days", [])):
        day = raw_day if isinstance(raw_day, dict) else {}
        raw_slots = day.get("slots", [])
        slots = raw_slots if isinstance(raw_slots, list) else []
        days.append(
            {
                "day_index": index,
                "day": DAY_MAP.get(index, str(index)),
                "exclude_day": bool(day.get("exclude_day", False)),
                "slots": [
                    {
                        "start_time": slot.get("start_time"),
                        "duration": slot.get("duration"),
                        "reason": slot.get("reason"),
                    }
                    for slot in slots
                    if isinstance(slot, dict)
                ],
            }
        )

    return {
        "enabled": bool(auto_schedule(device).get("enabled", False)),
        "exclude_nights": bool(exclusion.get("exclude_nights", False)),
        "days": days,
    }


def _normalized_schedule_attributes(schedule) -> dict[str, object] | None:
    """Return normalized schedule fields when available."""
    if schedule is None:
        return None

    protocol = int(getattr(schedule, "protocol"))
    entries = [
        {
            "entry_id": entry.entry_id,
            "day": entry.day,
            "start": entry.start,
            "duration": entry.duration,
            "boundary": entry.boundary,
            "source": entry.source,
            "secondary": entry.secondary,
            "label": _schedule_entry_label(
                day=entry.day,
                start=entry.start,
                duration=entry.duration,
                source=entry.source,
                protocol=protocol,
            ),
        }
        for entry in getattr(schedule, "entries", [])
    ]
    attributes: dict[str, object] = {
        "schedule_enabled": bool(getattr(schedule, "enabled", False)),
        "schedule_protocol": protocol,
        "schedule_entries": entries,
    }
    time_extension = getattr(schedule, "time_extension", None)
    if time_extension is not None:
        attributes["schedule_time_extension"] = int(time_extension)
    return attributes


def _schedule_attributes_with_normalized_schedule(
    device, schedule
) -> dict[str, object] | None:
    """Return known schedule fields merged with normalized schedule data."""
    schedules = getattr(device, "schedules", None)
    attributes: dict[str, object] = {}

    if isinstance(schedules, dict):
        known_keys = (
            "active",
            "time_extension",
            "slots",
            "party_mode_enabled",
            "one_time_schedule",
            "daily_progress",
            "next_schedule_start",
        )
        attributes.update(
            {
                key: schedules[key]
                for key in known_keys
                if key in schedules and schedules[key] is not None
            }
        )
        corrected_next = _next_schedule_value(device)
        if corrected_next is not None:
            attributes["next_schedule_start"] = corrected_next
        else:
            attributes.pop("next_schedule_start", None)

    normalized_attributes = _normalized_schedule_attributes(schedule)
    if normalized_attributes is not None:
        attributes.update(normalized_attributes)
    return attributes or None


def _schedule_entry_label(
    *,
    day: str,
    start: str,
    duration: int,
    source: str,
    protocol: int,
) -> str:
    """Return a human-readable schedule label."""
    label = f"{day.capitalize()} {start} ({duration} min)"
    if protocol == 0:
        label = f"{label} - {source}"
    return label


def _resolve_timezone(device) -> timezone | ZoneInfo:
    """Return the device timezone or UTC fallback."""
    tz_name = getattr(device, "time_zone", None)
    if tz_name is None:
        return UTC
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return UTC


def _next_schedule_value(device) -> datetime | None:
    """Return the next future slot with a non-zero duration."""
    schedules = getattr(device, "schedules", None)
    if not isinstance(schedules, dict):
        return None

    slots = schedules.get("slots", []) or []
    if not isinstance(slots, list):
        return None

    tzinfo = _resolve_timezone(device)
    now = datetime.now(tzinfo)
    candidates: list[datetime] = []

    for offset in range(0, 14):
        target_date = now + timedelta(days=offset)
        day = DAY_MAP[int(target_date.strftime("%w"))]
        for slot in slots:
            if slot.get("day") != day:
                continue
            if int(slot.get("duration_extended", 0)) <= 0:
                continue
            start_value = slot.get("start")
            if not isinstance(start_value, str):
                continue
            start = datetime.strptime(
                f"{target_date.strftime('%d/%m/%Y')} {start_value}:00",
                "%d/%m/%Y %H:%M:%S",
            ).replace(tzinfo=tzinfo)
            if offset == 0 and start <= now:
                continue
            candidates.append(start)

    if candidates:
        return min(candidates)

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
        key="error",
        translation_key="error",
        device_class=SensorDeviceClass.ENUM,
        options=ERROR_STATE_OPTIONS,
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
        key="nutrition",
        translation_key="auto_schedule_nutrition",
        entity_registry_enabled_default=False,
        icon="mdi:leaf",
        requires_auto_schedule=True,
    ),
    LandroidSensorDescription(
        key="exclusion_schedules",
        translation_key="auto_schedule_exclusion_schedules",
        entity_registry_enabled_default=False,
        icon="mdi:calendar-remove",
        requires_auto_schedule=True,
    ),
    LandroidSensorDescription(
        key="rain_delay_remaining",
        translation_key="rain_delay_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    LandroidSensorDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check",
        entity_registry_enabled_default=False,
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
        key="pitch",
        translation_key="pitch",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:axis-x-rotate-clockwise",
    ),
    LandroidSensorDescription(
        key="roll",
        translation_key="roll",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:axis-y-rotate-clockwise",
    ),
    LandroidSensorDescription(
        key="yaw",
        translation_key="yaw",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:axis-z-rotate-clockwise",
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
        key="blade_runtime_reset_at",
        translation_key="blade_runtime_reset_at",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:history",
    ),
    LandroidSensorDescription(
        key="blade_runtime_reset_time",
        translation_key="blade_runtime_reset_time",
        device_class=SensorDeviceClass.TIMESTAMP,
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
        self._attr_requires_auto_schedule = description.requires_auto_schedule
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def available(self) -> bool:
        """Return availability for sensors."""
        if not super().available:
            return False
        if self.entity_description.key == "next_schedule":
            return _next_schedule_value(self.device) is not None
        if self.entity_description.key == "rain_delay_remaining":
            return _rain_delay_remaining_value(self.device) is not None
        if self.entity_description.key == "daily_progress":
            return _daily_progress_value(self.device) is not None
        if self.entity_description.key == "nutrition":
            return _nutrition_value(self.device) is not None
        return True

    @property
    def native_value(self):
        """Return the native value for this sensor."""
        device = self.device
        key = self.entity_description.key

        if key == "battery":
            return device.battery.get("percent")
        if key == "error":
            return ERROR_STATE_MAP.get(device.error.get("id", -1), "unknown")
        if key == "rssi":
            return getattr(device, "rssi", None)
        if key == "daily_progress":
            return _daily_progress_value(device)
        if key == "next_schedule":
            return _next_schedule_value(device)
        if key == "nutrition":
            return _nutrition_value(device)
        if key == "exclusion_schedules":
            return _exclusion_schedule_value(device)
        if key == "rain_delay_remaining":
            return _rain_delay_remaining_value(device)
        if key == "last_update":
            return _last_update_value(device)
        if key == "battery_charge_cycles_total":
            return _battery_cycle_value(device, "total")
        if key == "battery_charge_cycles_current":
            return _battery_cycle_value(device, "current")
        if key == "battery_temperature":
            return _battery_value(device, "temperature")
        if key == "battery_voltage":
            return _battery_value(device, "voltage")
        if key == "pitch":
            return _orientation_value(device, "pitch")
        if key == "roll":
            return _orientation_value(device, "roll")
        if key == "yaw":
            return _orientation_value(device, "yaw")
        if key == "blade_runtime_total":
            return _blade_runtime_value(device, "total_on")
        if key == "blade_runtime_current":
            return _blade_runtime_value(device, "current_on")
        if key == "blade_runtime_reset_time":
            return _blade_reset_time_value(device)
        if key == "blade_runtime_reset_at":
            return _blade_runtime_value(device, "reset_at")
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
            return _schedule_attributes_with_normalized_schedule(
                self.device,
                self.coordinator.cloud.get_schedule(str(self.device.serial_number)),
            )
        if self.entity_description.key == "nutrition":
            return _nutrition_attributes(self.device)
        if self.entity_description.key == "exclusion_schedules":
            return _exclusion_schedule_attributes(self.device)
        return None
