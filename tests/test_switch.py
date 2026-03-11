"""Tests for Landroid switches."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.switch import SWITCHES


def test_switches_are_configuration_entities() -> None:
    """All switch entities should be categorized as configuration."""
    assert all(
        description.entity_category is EntityCategory.CONFIG
        for description in SWITCHES
    )
