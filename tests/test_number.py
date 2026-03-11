"""Tests for Landroid numbers."""

from types import SimpleNamespace

from custom_components.landroid_cloud.number import NUMBERS, _rain_delay_value


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
