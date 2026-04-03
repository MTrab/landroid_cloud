"""Tests for Landroid binary sensors."""

from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.binary_sensor import (
    BINARY_SENSORS,
    LandroidBinarySensor,
)


def test_rain_sensor_and_charging_are_diagnostic_entities() -> None:
    """Rain sensor and charging should be categorized as diagnostics."""
    rain_sensor = next(
        description
        for description in BINARY_SENSORS
        if description.key == "rain_sensor"
    )
    charging = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )

    assert rain_sensor.entity_category is EntityCategory.DIAGNOSTIC
    assert charging.entity_category is EntityCategory.DIAGNOSTIC


def test_charging_is_enabled_by_default_but_rain_sensor_is_not() -> None:
    """Charging should be enabled by default while rain sensor stays disabled."""
    rain_sensor = next(
        description
        for description in BINARY_SENSORS
        if description.key == "rain_sensor"
    )
    charging = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )

    assert rain_sensor.entity_registry_enabled_default is False
    assert charging.entity_registry_enabled_default is True


def test_charging_binary_sensor_is_unavailable_when_mower_is_offline() -> None:
    """Charging binary sensor should be unavailable while the mower is offline."""
    entity = object.__new__(LandroidBinarySensor)
    entity.entity_description = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={"serial": SimpleNamespace(online=False, battery={"charging": True})},
    )
    entity._serial_number = "serial"
    entity._attr_requires_online = entity.entity_description.requires_online

    assert entity.available is False
