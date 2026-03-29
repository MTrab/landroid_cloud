"""Tests for Landroid buttons."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.button import BUTTONS


def test_removed_buttons_are_not_exposed() -> None:
    """Restart and zone training should not be exposed as button entities."""
    keys = {description.key for description in BUTTONS}
    assert "restart" not in keys
    assert "zone_training" not in keys


def test_reset_buttons_are_configuration_entities() -> None:
    """Reset buttons should be categorized as configuration entities."""
    reset_keys = {"reset_blade_time", "reset_battery_cycles"}
    reset_buttons = [
        description for description in BUTTONS if description.key in reset_keys
    ]

    assert len(reset_buttons) == 2
    assert all(
        description.entity_category is EntityCategory.CONFIG
        for description in reset_buttons
    )


def test_edge_cut_is_disabled_by_default() -> None:
    """Edge cut should be disabled by default."""
    edge_cut = next(
        description for description in BUTTONS if description.key == "edge_cut"
    )

    assert edge_cut.entity_registry_enabled_default is False
