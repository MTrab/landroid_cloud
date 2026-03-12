"""Tests for Landroid selects."""

from types import SimpleNamespace

from custom_components.landroid_cloud.select import LandroidZoneSelect
from custom_components.landroid_cloud.select import _current_zone_option, _zone_options


def test_zone_select_is_disabled_by_default() -> None:
    """Zone select should be disabled by default."""
    entity = object.__new__(LandroidZoneSelect)

    assert entity.entity_registry_enabled_default is False


def test_zone_options_use_rtk_zone_ids_when_available() -> None:
    """RTK devices should expose their actual zone IDs as options."""
    device = SimpleNamespace(zone={"ids": [1, 2, 4, 5], "starting_point": [0, 0, 0, 0]})

    assert _zone_options(device) == ["1", "2", "4", "5"]


def test_current_zone_option_uses_rtk_current_zone() -> None:
    """RTK devices should expose the current RTK zone ID."""
    device = SimpleNamespace(zone={"ids": [1, 2, 4, 5], "current": 4, "index": 0})

    assert _current_zone_option(device) == "4"
