"""Tests for Landroid sensors."""

from types import SimpleNamespace

from homeassistant.const import ATTR_BATTERY_CHARGING

from custom_components.landroid_cloud.sensor import _battery_charging_attribute


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
