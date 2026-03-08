"""Tests for integration constants."""

from homeassistant.const import Platform

from custom_components.landroid_cloud.const import PLATFORMS


def test_platforms_use_home_assistant_platform_enum() -> None:
    """Sensor branch should expose mower + sensor platforms."""
    assert PLATFORMS == [Platform.LAWN_MOWER, Platform.SENSOR]
