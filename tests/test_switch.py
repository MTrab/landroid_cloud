"""Tests for Landroid switches."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.switch import SWITCHES


def test_switches_are_configuration_entities() -> None:
    """All switch entities should be categorized as configuration."""
    assert all(
        description.entity_category is EntityCategory.CONFIG
        for description in SWITCHES
    )


def test_party_mode_is_disabled_by_default() -> None:
    """Party mode should be disabled by default."""
    party_mode = next(
        description for description in SWITCHES if description.key == "party_mode"
    )

    assert party_mode.entity_registry_enabled_default is False
