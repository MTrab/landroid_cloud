"""Tests for Landroid Cloud config flow schema."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.selector import SelectSelector

from custom_components.landroid_cloud.config_flow import (
    STEP_USER_DATA_SCHEMA,
    LandroidCloudOptionsFlow,
)
from custom_components.landroid_cloud.const import CONF_CLOUD, CONF_COMMAND_TIMEOUT


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


@pytest.mark.asyncio
async def test_options_flow_shows_account_fields_without_command_timeout() -> None:
    """Options flow should expose account credentials, not command timeout."""
    entry = SimpleNamespace(
        data={
            CONF_EMAIL: "user@example.com",
            CONF_PASSWORD: "old-secret",
            CONF_CLOUD: "worx",
        },
        options={CONF_COMMAND_TIMEOUT: 12.0},
        entry_id="entry-1",
        unique_id="user@example.com::worx",
    )
    flow = LandroidCloudOptionsFlow(entry)

    result = await flow.async_step_init()

    assert result["step_id"] == "init"
    schema_keys = {key.schema for key in result["data_schema"].schema}
    assert schema_keys == {CONF_EMAIL, CONF_PASSWORD}
    assert CONF_COMMAND_TIMEOUT not in schema_keys


@pytest.mark.asyncio
async def test_options_flow_updates_account_credentials(monkeypatch) -> None:
    """Submitting options should validate and persist new account credentials."""
    entry = SimpleNamespace(
        data={
            CONF_EMAIL: "user@example.com",
            CONF_PASSWORD: "old-secret",
            CONF_CLOUD: "worx",
        },
        options={CONF_COMMAND_TIMEOUT: 12.0},
        entry_id="entry-1",
        unique_id="user@example.com::worx",
    )
    updates: list[dict[str, object]] = []

    class ConfigEntries:
        """Minimal config entries manager for options flow tests."""

        def async_entries(self, domain: str):
            assert domain == "landroid_cloud"
            return [entry]

        def async_update_entry(self, _entry, **kwargs):
            updates.append(kwargs)
            return True

    async def validate_input(user_input):
        assert user_input == {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-secret",
            CONF_CLOUD: "worx",
        }
        return {"title": "new@example.com (worx)", "device_count": 1}

    monkeypatch.setattr(
        "custom_components.landroid_cloud.config_flow._validate_input",
        validate_input,
    )

    flow = LandroidCloudOptionsFlow(entry)
    flow.hass = SimpleNamespace(config_entries=ConfigEntries())

    result = await flow.async_step_init(
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-secret",
        }
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {}
    assert updates == [
        {
            "data": {
                CONF_EMAIL: "new@example.com",
                CONF_PASSWORD: "new-secret",
                CONF_CLOUD: "worx",
            },
            "title": "new@example.com (worx)",
            "unique_id": "new@example.com::worx",
        }
    ]
