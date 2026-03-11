"""Tests for Landroid selects."""

from custom_components.landroid_cloud.select import LandroidZoneSelect


def test_zone_select_is_disabled_by_default() -> None:
    """Zone select should be disabled by default."""
    entity = object.__new__(LandroidZoneSelect)

    assert entity.entity_registry_enabled_default is False
