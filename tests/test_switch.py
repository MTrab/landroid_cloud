"""Tests for Landroid switches."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.switch import SWITCHES


def test_switches_are_configuration_entities() -> None:
    """All switch entities should be categorized as configuration."""
    assert all(
        description.entity_category is EntityCategory.CONFIG
        for description in SWITCHES
    )


def test_pause_mode_is_disabled_by_default() -> None:
    """Pause mode should be disabled by default."""
    pause_mode = next(
        description for description in SWITCHES if description.key == "pause_mode"
    )

    assert pause_mode.entity_registry_enabled_default is False
