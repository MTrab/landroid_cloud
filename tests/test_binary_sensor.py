"""Tests for Landroid binary sensors."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.binary_sensor import BINARY_SENSORS


def test_rain_sensor_and_charging_are_diagnostic_entities() -> None:
    """Rain sensor and charging should be categorized as diagnostics."""
    rain_sensor = next(
        description for description in BINARY_SENSORS if description.key == "rain_sensor"
    )
    charging = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )

    assert rain_sensor.entity_category is EntityCategory.DIAGNOSTIC
    assert charging.entity_category is EntityCategory.DIAGNOSTIC
