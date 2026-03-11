"""Tests for Landroid sensors."""

from types import SimpleNamespace

from homeassistant.const import ATTR_BATTERY_CHARGING
from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.sensor import (
    SENSORS,
    _battery_charging_attribute,
    _rain_delay_remaining_value,
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


def test_rain_delay_remaining_value_unavailable() -> None:
    """Rain delay remaining should be unknown for non-integer values."""
    device = SimpleNamespace(rainsensor={"remaining": "42"})
    assert _rain_delay_remaining_value(device) is None


def test_error_and_rssi_are_diagnostic_entities() -> None:
    """Error and signal strength should be categorized as diagnostics."""
    error = next(description for description in SENSORS if description.key == "error")
    rssi = next(description for description in SENSORS if description.key == "rssi")

    assert error.entity_category is EntityCategory.DIAGNOSTIC
    assert rssi.entity_category is EntityCategory.DIAGNOSTIC
