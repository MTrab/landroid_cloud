"""Tests for Landroid binary sensors."""

from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.binary_sensor import (
    BINARY_SENSORS,
    LandroidBinarySensor,
)


def test_binary_sensors_are_diagnostic_entities() -> None:
    """Binary sensors should be categorized as diagnostics."""
    mqtt_connected = next(
        description
        for description in BINARY_SENSORS
        if description.key == "mqtt_connected"
    )
    rain_sensor = next(
        description
        for description in BINARY_SENSORS
        if description.key == "rain_sensor"
    )
    charging = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )

    assert mqtt_connected.entity_category is EntityCategory.DIAGNOSTIC
    assert rain_sensor.entity_category is EntityCategory.DIAGNOSTIC
    assert charging.entity_category is EntityCategory.DIAGNOSTIC


def test_charging_and_mqtt_connected_are_enabled_by_default_but_rain_sensor_is_not() -> (
    None
):
    """Charging and MQTT connected should be enabled by default."""
    mqtt_connected = next(
        description
        for description in BINARY_SENSORS
        if description.key == "mqtt_connected"
    )
    rain_sensor = next(
        description
        for description in BINARY_SENSORS
        if description.key == "rain_sensor"
    )
    charging = next(
        description for description in BINARY_SENSORS if description.key == "charging"
    )

    assert mqtt_connected.entity_registry_enabled_default is True
    assert rain_sensor.entity_registry_enabled_default is False
    assert charging.entity_registry_enabled_default is True


def test_mqtt_connected_reads_cloud_property() -> None:
    """MQTT connected should expose the pyworxcloud cloud property."""
    entity = object.__new__(LandroidBinarySensor)
    entity.entity_description = next(
        description
        for description in BINARY_SENSORS
        if description.key == "mqtt_connected"
    )
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(mqtt_connected=True),
        data={"serial": SimpleNamespace()},
    )
    entity._serial_number = "serial"

    assert entity.is_on is True


def test_mqtt_connected_is_unknown_without_boolean_cloud_property() -> None:
    """MQTT connected should be unknown when pyworxcloud has no boolean value."""
    entity = object.__new__(LandroidBinarySensor)
    entity.entity_description = next(
        description
        for description in BINARY_SENSORS
        if description.key == "mqtt_connected"
    )
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(mqtt_connected=None),
        data={"serial": SimpleNamespace()},
    )
    entity._serial_number = "serial"

    assert entity.is_on is None


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
