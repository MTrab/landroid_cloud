"""Tests for integration constants."""

from homeassistant.const import Platform

from custom_components.landroid_cloud.const import PLATFORMS


def test_platforms_use_home_assistant_platform_enum() -> None:
    """Merged branch should expose mower, sensor, switch, and binary sensor."""
    assert PLATFORMS == [
        Platform.LAWN_MOWER,
        Platform.SENSOR,
        Platform.SWITCH,
        Platform.BINARY_SENSOR,
    ]
