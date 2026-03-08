"""Tests for mower activity mapping."""

from homeassistant.components.lawn_mower import LawnMowerActivity

from custom_components.landroid_cloud.lawn_mower import STATUS_ACTIVITY_MAP


def test_start_sequence_states_map_to_mowing() -> None:
    """Start-sequence related status codes should map to standard mowing state."""
    assert STATUS_ACTIVITY_MAP[2] is LawnMowerActivity.MOWING
    assert STATUS_ACTIVITY_MAP[3] is LawnMowerActivity.MOWING


def test_unknown_state_defaults_to_error() -> None:
    """Unknown status ids should not map to non-standard activities."""
    assert STATUS_ACTIVITY_MAP.get(999, LawnMowerActivity.ERROR) is LawnMowerActivity.ERROR
