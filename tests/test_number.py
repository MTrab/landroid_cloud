"""Tests for Landroid numbers."""

from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.number import (
    NUMBERS,
    _lawn_value,
    _rain_delay_value,
    _torque_value,
    _time_extension_value,
)


def test_numbers_are_disabled_by_default() -> None:
    """Number entities should be disabled by default."""
    assert all(
        description.entity_registry_enabled_default is False for description in NUMBERS
    )


def test_rain_delay_value_is_exposed_without_decimals() -> None:
    """Rain delay should be represented as an integer value."""
    device = SimpleNamespace(rainsensor={"delay": 30})
    value = _rain_delay_value(device)

    assert isinstance(value, int)
    assert value == 30


def test_time_extension_value_is_exposed_without_decimals() -> None:
    """Time extension should be represented as an integer percentage."""
    device = SimpleNamespace(schedules={"time_extension": 15})
    value = _time_extension_value(device)

    assert isinstance(value, int)
    assert value == 15


def test_torque_value_is_exposed_without_decimals() -> None:
    """Torque should be represented as an integer percentage."""
    device = SimpleNamespace(torque=-13)
    value = _torque_value(device)

    assert isinstance(value, int)
    assert value == -13


def test_lawn_values_are_exposed_without_decimals() -> None:
    """Lawn size and perimeter should be represented as integer values."""
    device = SimpleNamespace(lawn={"size": 250, "perimeter": 115})

    assert _lawn_value(device, "size") == 250
    assert _lawn_value(device, "perimeter") == 115


def test_time_extension_is_configuration_entity() -> None:
    """Time extension should be exposed as a configuration number."""
    description = next(
        description for description in NUMBERS if description.key == "time_extension"
    )

    assert description.entity_category is EntityCategory.CONFIG
    assert description.native_min_value == -100
    assert description.native_max_value == 100
    assert description.native_step == 10


def test_torque_is_configuration_entity() -> None:
    """Torque should be exposed as a disabled configuration number."""
    description = next(
        description for description in NUMBERS if description.key == "torque"
    )

    assert description.entity_category is EntityCategory.CONFIG
    assert description.entity_registry_enabled_default is False
    assert description.native_min_value == -50
    assert description.native_max_value == 50
    assert description.native_step == 1
    assert description.native_unit_of_measurement == "%"
    assert description.icon == "mdi:gauge"


def test_lawn_numbers_are_configuration_entities() -> None:
    """Lawn size and perimeter should be exposed as disabled configuration numbers."""
    descriptions = {description.key: description for description in NUMBERS}

    lawn_size = descriptions["lawn_size"]
    assert lawn_size.entity_category is EntityCategory.CONFIG
    assert lawn_size.entity_registry_enabled_default is False
    assert lawn_size.native_min_value == 0
    assert lawn_size.native_max_value == 100000
    assert lawn_size.native_step == 1
    assert lawn_size.native_unit_of_measurement == "m²"
    assert lawn_size.icon == "mdi:texture-box"

    lawn_perimeter = descriptions["lawn_perimeter"]
    assert lawn_perimeter.entity_category is EntityCategory.CONFIG
    assert lawn_perimeter.entity_registry_enabled_default is False
    assert lawn_perimeter.native_min_value == 0
    assert lawn_perimeter.native_max_value == 100000
    assert lawn_perimeter.native_step == 1
    assert lawn_perimeter.native_unit_of_measurement == "m"
    assert lawn_perimeter.icon == "mdi:ruler-square"


def test_rain_delay_max_value_is_1440_minutes() -> None:
    """Rain delay max value should be 1440 minutes (24 hours) to match app."""
    rain_delay_desc = next(desc for desc in NUMBERS if desc.key == "rain_delay")
    assert rain_delay_desc.native_max_value == 1440
