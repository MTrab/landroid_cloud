"""Tests for Landroid Cloud config flow schema."""

import json
from pathlib import Path

from homeassistant.helpers.selector import SelectSelector

from custom_components.landroid_cloud.config_flow import STEP_USER_DATA_SCHEMA


def test_cloud_selector_uses_translated_labels() -> None:
    """Cloud selector should expose translation-backed option labels."""
    selector = STEP_USER_DATA_SCHEMA.schema["cloud"]

    assert isinstance(selector, SelectSelector)
    assert selector.config["translation_key"] == "cloud"
    assert selector.config["options"] == ["worx", "kress", "landxcape"]


def test_abort_translation_covers_already_in_progress() -> None:
    """All locale files should include the already_in_progress abort string."""
    translation_dir = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "landroid_cloud"
        / "translations"
    )

    for translation_file in translation_dir.glob("*.json"):
        content = json.loads(translation_file.read_text())
        assert content["config"]["abort"]["already_in_progress"], (
            f"Missing already_in_progress abort translation for {translation_file.name}"
        )
