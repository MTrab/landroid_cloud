"""Tests for integration constants."""

from homeassistant.const import Platform

from custom_components.landroid_cloud.const import PLATFORMS


def test_platforms_use_home_assistant_platform_enum() -> None:
    """Only supported lawn mower platform should be exposed."""
    assert PLATFORMS == [Platform.LAWN_MOWER]
