"""Tests for Landroid selects."""

from types import SimpleNamespace

from custom_components.landroid_cloud.select import AUTO_SCHEDULE_SELECTS
from custom_components.landroid_cloud.select import LandroidAutoScheduleSelect
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


def test_auto_schedule_selects_use_pyworxcloud_valid_options() -> None:
    """Auto-schedule selects should only expose pyworxcloud-supported values."""
    descriptions = {
        description.key: description for description in AUTO_SCHEDULE_SELECTS
    }

    assert descriptions["auto_schedule_boost"].options == ("0", "1", "2")
    assert descriptions["auto_schedule_grass_type"].options == (
        "mixed_species",
        "festuca_arundinacea",
        "lolium_perenne",
        "poa_pratensis",
        "festuca_rubra",
        "agrostis_stolonifera",
    )
    assert descriptions["auto_schedule_soil_type"].options == (
        "clay",
        "silt",
        "sand",
        "ignore",
    )


def test_auto_schedule_selects_have_distinct_icons() -> None:
    """Auto-schedule selects should expose meaningful icons in the UI."""
    descriptions = {
        description.key: description for description in AUTO_SCHEDULE_SELECTS
    }

    assert descriptions["auto_schedule_boost"].icon == "mdi:speedometer"
    assert descriptions["auto_schedule_grass_type"].icon == "mdi:grass"
    assert descriptions["auto_schedule_soil_type"].icon == "mdi:shovel"


def test_auto_schedule_select_is_unavailable_when_auto_schedule_is_disabled() -> None:
    """Dependent auto-schedule selects should be unavailable when disabled."""
    entity = object.__new__(LandroidAutoScheduleSelect)
    entity._serial_number = "serial"
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = True
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                online=True,
                schedules={"auto_schedule": {"enabled": False, "settings": {}}},
            )
        },
    )

    assert entity.available is False


def test_zone_options_only_include_configured_legacy_zones() -> None:
    """Legacy devices should only expose zones with configured start points."""
    device = SimpleNamespace(
        zone={"ids": [], "starting_point": [1, 7, 0, 0], "current": 1, "index": 3}
    )

    assert _zone_options(device) == ["1", "2"]


def test_current_zone_option_prefers_reported_legacy_zone() -> None:
    """Legacy devices should display the reported current zone before fallback index."""
    device = SimpleNamespace(
        zone={"ids": [], "starting_point": [1, 7, 0, 0], "current": 1, "index": 3}
    )

    assert _current_zone_option(device) == "1"
