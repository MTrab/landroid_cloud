"""Tests for Landroid Cloud config flow schema."""

from homeassistant.helpers.selector import SelectSelector

from custom_components.landroid_cloud.config_flow import STEP_USER_DATA_SCHEMA


def test_cloud_selector_uses_translated_labels() -> None:
    """Cloud selector should expose translation-backed option labels."""
    selector = STEP_USER_DATA_SCHEMA.schema["cloud"]

    assert isinstance(selector, SelectSelector)
    assert selector.config["translation_key"] == "cloud"
    assert selector.config["options"] == ["worx", "kress", "landxcape"]
