"""Tests for integration constants."""

from homeassistant.const import Platform

from custom_components.landroid_cloud.const import PLATFORMS


def test_platforms_use_home_assistant_platform_enum() -> None:
    """Binary sensor branch should expose mower + sensor + binary sensor."""
    assert PLATFORMS == [
        Platform.LAWN_MOWER,
        Platform.SENSOR,
        Platform.BINARY_SENSOR,
    ]
