"""Tests for Landroid switches."""

from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.switch import LandroidSwitch, SWITCHES


def test_switches_are_configuration_entities() -> None:
    """All switch entities should be categorized as configuration."""
    assert all(
        description.entity_category is EntityCategory.CONFIG for description in SWITCHES
    )


def test_party_mode_is_disabled_by_default() -> None:
    """Party mode should be disabled by default."""
    party_mode = next(
        description for description in SWITCHES if description.key == "party_mode"
    )

    assert party_mode.entity_registry_enabled_default is False


def test_auto_schedule_switch_is_disabled_by_default() -> None:
    """Auto schedule should be disabled by default."""
    auto_schedule = next(
        description for description in SWITCHES if description.key == "auto_schedule"
    )

    assert auto_schedule.entity_registry_enabled_default is False


def test_irrigation_and_exclude_nights_are_disabled_by_default() -> None:
    """Auto-schedule switches should be disabled by default."""
    irrigation = next(
        description for description in SWITCHES if description.key == "irrigation"
    )
    exclude_nights = next(
        description for description in SWITCHES if description.key == "exclude_nights"
    )

    assert irrigation.entity_registry_enabled_default is False
    assert exclude_nights.entity_registry_enabled_default is False


def test_acs_is_disabled_by_default() -> None:
    """ACS should be disabled by default."""
    acs = next(description for description in SWITCHES if description.key == "acs")

    assert acs.entity_registry_enabled_default is False


def test_auto_schedule_dependent_switch_is_unavailable_when_disabled() -> None:
    """Dependent auto-schedule switches should be unavailable when disabled."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description for description in SWITCHES if description.key == "irrigation"
    )
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
