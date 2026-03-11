"""Tests for Landroid numbers."""

from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.number import (
    NUMBERS,
    _rain_delay_value,
    _time_extension_value,
)


def test_numbers_are_disabled_by_default() -> None:
    """Number entities should be disabled by default."""
    assert all(
        description.entity_registry_enabled_default is False
        for description in NUMBERS
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


def test_time_extension_is_configuration_entity() -> None:
    """Time extension should be exposed as a configuration number."""
    description = next(
        description for description in NUMBERS if description.key == "time_extension"
    )

    assert description.entity_category is EntityCategory.CONFIG
    assert description.native_min_value == -100
    assert description.native_max_value == 100
    assert description.native_step == 10
