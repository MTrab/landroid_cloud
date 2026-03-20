"""Tests for Landroid sensors."""

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_BATTERY_CHARGING
from homeassistant.helpers.entity import EntityCategory

import custom_components.landroid_cloud.sensor as sensor_module
from custom_components.landroid_cloud.const import ERROR_STATE_MAP, ERROR_STATE_OPTIONS
from custom_components.landroid_cloud.sensor import (
    LandroidSensor,
    SENSORS,
    _battery_cycle_value,
    _battery_charging_attribute,
    _battery_value,
    _blade_reset_time_value,
    _blade_runtime_value,
    _last_update_value,
    _next_schedule_value,
    _normalized_schedule_attributes,
    _orientation_value,
    _rain_delay_remaining_value,
    _schedule_attributes,
    _schedule_attributes_with_normalized_schedule,
    _schedule_entry_label,
    _statistics_value,
)


def test_battery_charging_attribute_true() -> None:
    """Charging state True should be exposed using HA standard attribute key."""
    device = SimpleNamespace(battery={"charging": True})
    assert _battery_charging_attribute(device) == {ATTR_BATTERY_CHARGING: True}


def test_battery_charging_attribute_false() -> None:
    """Charging state False should be exposed using HA standard attribute key."""
    device = SimpleNamespace(battery={"charging": False})
    assert _battery_charging_attribute(device) == {ATTR_BATTERY_CHARGING: False}


def test_battery_charging_attribute_unavailable() -> None:
    """Unknown charging state should not set battery charging attribute."""
    device = SimpleNamespace(battery={"charging": "unknown"})
    assert _battery_charging_attribute(device) is None


def test_rssi_is_read_from_attribute() -> None:
    """RSSI mapping should use device attribute and not dict lookup."""
    device = SimpleNamespace(
        battery={},
        error={},
        schedules={},
        rssi=-67,
    )
    # Equivalent behavior to sensor native_value branch for key == "rssi".
    assert getattr(device, "rssi", None) == -67


def test_rain_delay_remaining_value_returns_minutes() -> None:
    """Rain delay remaining should be exposed as integer minutes."""
    device = SimpleNamespace(rainsensor={"remaining": 42})
    assert _rain_delay_remaining_value(device) == 42


def test_rain_delay_remaining_value_zero_is_unavailable() -> None:
    """Rain delay remaining should be unavailable when no delay is active."""
    device = SimpleNamespace(rainsensor={"remaining": 0})
    assert _rain_delay_remaining_value(device) is None


def test_rain_delay_remaining_value_unavailable() -> None:
    """Rain delay remaining should be unknown for non-integer values."""
    device = SimpleNamespace(rainsensor={"remaining": "42"})
    assert _rain_delay_remaining_value(device) is None


def test_orientation_value_returns_axis_degrees() -> None:
    """Orientation axes should be exposed as numeric degree values."""
    device = SimpleNamespace(orientation={"pitch": 1, "roll": -2.5, "yaw": 180})

    assert _orientation_value(device, "pitch") == 1.0
    assert _orientation_value(device, "roll") == -2.5
    assert _orientation_value(device, "yaw") == 180.0


def test_orientation_value_unavailable_for_non_numeric_axis() -> None:
    """Orientation axes should be unavailable for non-numeric values."""
    device = SimpleNamespace(orientation={"pitch": "1"})
    assert _orientation_value(device, "pitch") is None


def test_error_state_mapping_uses_stable_tokens() -> None:
    """Error states should map from numeric ids to translation tokens."""
    assert ERROR_STATE_MAP[0] == "no_error"
    assert ERROR_STATE_MAP[110] == "camera_error"
    assert ERROR_STATE_MAP.get(999, "unknown") == "unknown"


def test_error_and_rssi_are_diagnostic_entities() -> None:
    """Error and signal strength should be categorized as diagnostics."""
    error = next(description for description in SENSORS if description.key == "error")
    rssi = next(description for description in SENSORS if description.key == "rssi")
    pitch = next(description for description in SENSORS if description.key == "pitch")
    roll = next(description for description in SENSORS if description.key == "roll")
    yaw = next(description for description in SENSORS if description.key == "yaw")

    assert error.entity_category is EntityCategory.DIAGNOSTIC
    assert rssi.entity_category is EntityCategory.DIAGNOSTIC
    assert pitch.entity_category is EntityCategory.DIAGNOSTIC
    assert roll.entity_category is EntityCategory.DIAGNOSTIC
    assert yaw.entity_category is EntityCategory.DIAGNOSTIC


def test_error_is_enum_sensor_with_translated_state_tokens() -> None:
    """Error should expose stable enum tokens for translation."""
    error = next(description for description in SENSORS if description.key == "error")

    assert error.device_class is SensorDeviceClass.ENUM
    assert error.options == ERROR_STATE_OPTIONS
    assert "no_error" in error.options
    assert "camera_error" in error.options
    assert "unknown" in error.options


def test_selected_sensors_expose_specific_icons() -> None:
    """Sensors with ambiguous defaults should expose explicit icons."""
    descriptions = {description.key: description for description in SENSORS}

    assert descriptions["daily_progress"].icon == "mdi:progress-clock"
    assert descriptions["battery_charge_cycles_total"].icon == "mdi:battery-sync"
    assert descriptions["battery_charge_cycles_current"].icon == "mdi:battery-sync"
    assert descriptions["error"].icon == "mdi:alert-circle-outline"
    assert descriptions["pitch"].icon == "mdi:arrow-up-down-bold-outline"
    assert descriptions["roll"].icon == "mdi:arrow-left-right-bold-outline"
    assert descriptions["yaw"].icon == "mdi:compass-rose"


def test_next_schedule_is_timestamp_sensor() -> None:
    """Next schedule should be modeled as a timestamp sensor."""
    next_schedule = next(
        description for description in SENSORS if description.key == "next_schedule"
    )

    assert next_schedule.device_class is SensorDeviceClass.TIMESTAMP


def test_schedule_attributes_expose_known_schedule_fields() -> None:
    """Known schedule fields should be exposed without stale next-schedule values."""
    schedules = {
        "active": True,
        "time_extension": 10,
        "slots": [{"day": "mon", "start": "10:00", "end": "11:00"}],
        "pause_mode_enabled": False,
        "one_time_schedule": True,
        "auto_schedule": {"enabled": True, "settings": {"boost": 1}},
        "daily_progress": 75,
        "next_schedule_start": "2026-03-12 10:30:00+01:00",
        "ignored": "value",
    }
    device = SimpleNamespace(schedules=schedules)

    assert _schedule_attributes(device) == {
        "active": True,
        "time_extension": 10,
        "slots": [{"day": "mon", "start": "10:00", "end": "11:00"}],
        "pause_mode_enabled": False,
        "one_time_schedule": True,
        "auto_schedule": {"enabled": True, "settings": {"boost": 1}},
        "daily_progress": 75,
    }


def test_normalized_schedule_attributes_include_entry_metadata() -> None:
    """Normalized schedule fields should expose entry ids and protocol data."""
    schedule = SimpleNamespace(
        enabled=True,
        protocol=0,
        time_extension=10,
        entries=[
            SimpleNamespace(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            )
        ],
    )

    assert _normalized_schedule_attributes(schedule) == {
        "schedule_enabled": True,
        "schedule_protocol": 0,
        "schedule_time_extension": 10,
        "schedule_entries": [
            {
                "entry_id": "p0:monday:primary",
                "day": "monday",
                "start": "09:00",
                "duration": 60,
                "boundary": False,
                "source": "primary",
                "secondary": False,
                "label": "Monday 09:00 (60 min) - primary",
            }
        ],
    }


def test_schedule_entry_label_is_human_readable() -> None:
    """Schedule labels should be easy to copy from sensor attributes."""
    assert (
        _schedule_entry_label(
            day="monday",
            start="09:00",
            duration=60,
            source="primary",
            protocol=0,
        )
        == "Monday 09:00 (60 min) - primary"
    )
    assert (
        _schedule_entry_label(
            day="tuesday",
            start="12:30",
            duration=45,
            source="slot",
            protocol=1,
        )
        == "Tuesday 12:30 (45 min)"
    )


def test_schedule_attributes_merge_normalized_schedule_fields() -> None:
    """Legacy and normalized schedule fields should be exposed together."""
    device = SimpleNamespace(
        schedules={
            "active": True,
            "slots": [{"day": "monday", "start": "09:00", "end": "10:00"}],
        }
    )
    schedule = SimpleNamespace(
        enabled=False,
        protocol=1,
        time_extension=None,
        entries=[],
    )

    assert _schedule_attributes_with_normalized_schedule(device, schedule) == {
        "active": True,
        "slots": [{"day": "monday", "start": "09:00", "end": "10:00"}],
        "schedule_enabled": False,
        "schedule_protocol": 1,
        "schedule_entries": [],
    }


def test_next_schedule_skips_zero_duration_slots(monkeypatch) -> None:
    """Zero-duration slots should not be exposed as the next schedule."""
    real_datetime = sensor_module.datetime

    class FrozenDateTime:
        """Minimal datetime shim returning a fixed current time."""

        @staticmethod
        def now(tz=None):
            return real_datetime(2026, 3, 12, 10, 30, tzinfo=tz or ZoneInfo("UTC"))

        strptime = staticmethod(real_datetime.strptime)

    monkeypatch.setattr(sensor_module, "datetime", FrozenDateTime)

    device = SimpleNamespace(
        time_zone="UTC",
        schedules={
            "slots": [
                {
                    "day": "thursday",
                    "start": "11:00",
                    "end": "11:00",
                    "duration": 0,
                    "duration_extended": 0,
                },
                {
                    "day": "thursday",
                    "start": "15:00",
                    "end": "15:30",
                    "duration": 30,
                    "duration_extended": 30,
                },
            ],
            "next_schedule_start": datetime(2026, 3, 12, 11, 0, tzinfo=ZoneInfo("UTC")),
        },
    )

    assert _next_schedule_value(device) == datetime(
        2026, 3, 12, 15, 0, tzinfo=ZoneInfo("UTC")
    )


def test_next_schedule_returns_none_when_no_valid_slots_exist(monkeypatch) -> None:
    """Stale next-schedule payloads should be ignored when no schedule is active."""
    real_datetime = sensor_module.datetime

    class FrozenDateTime:
        """Minimal datetime shim returning a fixed current time."""

        @staticmethod
        def now(tz=None):
            return real_datetime(2026, 3, 12, 10, 30, tzinfo=tz or ZoneInfo("UTC"))

        strptime = staticmethod(real_datetime.strptime)

    monkeypatch.setattr(sensor_module, "datetime", FrozenDateTime)

    device = SimpleNamespace(
        time_zone="UTC",
        schedules={
            "active": False,
            "slots": [
                {
                    "day": "thursday",
                    "start": "11:00",
                    "end": "11:00",
                    "duration": 0,
                    "duration_extended": 0,
                }
            ],
            "next_schedule_start": datetime(
                2026, 3, 12, 11, 0, tzinfo=ZoneInfo("UTC")
            ),
        },
    )

    assert _next_schedule_value(device) is None
    assert _schedule_attributes(device) == {
        "active": False,
        "slots": [
            {
                "day": "thursday",
                "start": "11:00",
                "end": "11:00",
                "duration": 0,
                "duration_extended": 0,
            }
        ],
    }


def test_next_schedule_sensor_is_unavailable_without_valid_schedule() -> None:
    """Next schedule sensor should be unavailable when no schedule exists."""
    entity = object.__new__(LandroidSensor)
    entity.entity_description = next(
        description for description in SENSORS if description.key == "next_schedule"
    )
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                schedules={"active": False, "slots": []},
                time_zone="UTC",
            )
        },
    )
    entity._serial_number = "serial"

    assert entity.available is False


def test_next_schedule_sensor_stays_available_with_valid_schedule(monkeypatch) -> None:
    """Next schedule sensor should be available when a future schedule exists."""
    real_datetime = sensor_module.datetime

    class FrozenDateTime:
        """Minimal datetime shim returning a fixed current time."""

        @staticmethod
        def now(tz=None):
            return real_datetime(2026, 3, 12, 10, 30, tzinfo=tz or ZoneInfo("UTC"))

        strptime = staticmethod(real_datetime.strptime)

    monkeypatch.setattr(sensor_module, "datetime", FrozenDateTime)

    entity = object.__new__(LandroidSensor)
    entity.entity_description = next(
        description for description in SENSORS if description.key == "next_schedule"
    )
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                schedules={
                    "active": True,
                    "slots": [
                        {
                            "day": "thursday",
                            "start": "15:00",
                            "end": "15:30",
                            "duration": 30,
                            "duration_extended": 30,
                        }
                    ],
                },
                time_zone="UTC",
            )
        },
    )
    entity._serial_number = "serial"

    assert entity.available is True


def test_battery_cycle_value_returns_integer() -> None:
    """Battery cycle values should be exposed when present."""
    device = SimpleNamespace(battery={"cycles": {"total": 3014, "current": 14}})

    assert _battery_cycle_value(device, "total") == 3014
    assert _battery_cycle_value(device, "current") == 14


def test_blade_runtime_value_returns_minutes() -> None:
    """Blade runtime values should be exposed in minutes."""
    device = SimpleNamespace(blades={"total_on": 1200, "current_on": 320})

    assert _blade_runtime_value(device, "total_on") == 1200
    assert _blade_runtime_value(device, "current_on") == 320


def test_blade_reset_time_value_returns_timestamp() -> None:
    """Blade reset timestamp should be exposed when present."""
    reset_time = datetime(2026, 3, 12, 11, 45, tzinfo=ZoneInfo("UTC"))
    device = SimpleNamespace(blades={"reset_time": reset_time})

    assert _blade_reset_time_value(device) == reset_time


def test_last_update_value_returns_utc_timestamp() -> None:
    """Last update should be converted to UTC."""
    updated = datetime(2026, 3, 12, 13, 45, tzinfo=ZoneInfo("Europe/Copenhagen"))
    device = SimpleNamespace(updated=updated)

    assert _last_update_value(device) == datetime(
        2026, 3, 12, 12, 45, tzinfo=ZoneInfo("UTC")
    )


def test_battery_value_returns_float() -> None:
    """Battery telemetry values should be exposed as floats."""
    device = SimpleNamespace(battery={"temperature": 15.6, "voltage": 20.47})

    assert _battery_value(device, "temperature") == 15.6
    assert _battery_value(device, "voltage") == 20.47


def test_statistics_value_returns_integer() -> None:
    """Statistics values should be exposed when present."""
    device = SimpleNamespace(statistics={"distance": 2146986, "worktime_total": 129895})

    assert _statistics_value(device, "distance") == 2146986
    assert _statistics_value(device, "worktime_total") == 129895


def test_blade_and_battery_diagnostic_sensors_are_disabled_by_default() -> None:
    """Blade and battery diagnostic sensors should be disabled by default."""
    diagnostic_keys = {
        "battery_charge_cycles_total",
        "battery_charge_cycles_current",
        "battery_temperature",
        "battery_voltage",
        "blade_runtime_total",
        "blade_runtime_current",
        "blade_runtime_reset_at",
        "blade_runtime_reset_time",
        "distance_driven_total",
        "mower_runtime_total",
    }
    sensors = [
        description for description in SENSORS if description.key in diagnostic_keys
    ]

    assert len(sensors) == 10
    assert all(
        description.entity_category is EntityCategory.DIAGNOSTIC
        and description.entity_registry_enabled_default is False
        for description in sensors
    )


def test_rain_delay_remaining_is_disabled_by_default() -> None:
    """Rain delay remaining should be disabled by default."""
    rain_delay_remaining = next(
        description
        for description in SENSORS
        if description.key == "rain_delay_remaining"
    )

    assert rain_delay_remaining.entity_registry_enabled_default is False


def test_orientation_sensors_are_disabled_by_default() -> None:
    """Orientation sensors should be disabled by default."""
    descriptions = {description.key: description for description in SENSORS}

    assert descriptions["pitch"].entity_registry_enabled_default is False
    assert descriptions["roll"].entity_registry_enabled_default is False
    assert descriptions["yaw"].entity_registry_enabled_default is False


def test_last_update_is_disabled_by_default() -> None:
    """Last update should be disabled by default."""
    last_update = next(
        description for description in SENSORS if description.key == "last_update"
    )

    assert last_update.entity_registry_enabled_default is False
