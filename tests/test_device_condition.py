"""Tests for Landroid Cloud device conditions."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.const import (
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
import pytest

from custom_components.landroid_cloud import DOMAIN
from custom_components.landroid_cloud.device_condition import (
    async_condition_from_config,
    async_get_conditions,
)


@pytest.mark.asyncio
async def test_get_conditions_returns_supported_mower_conditions(
    monkeypatch,
) -> None:
    """Device conditions should be exposed for mower entities only."""
    registry = object()
    mower_entry = SimpleNamespace(
        domain="lawn_mower",
        platform=DOMAIN,
        id="registry-entry-id",
        entity_id="lawn_mower.front_yard",
    )
    ignored_entry = SimpleNamespace(
        domain="lawn_mower",
        platform="other_integration",
        id="other-entry",
        entity_id="lawn_mower.other",
    )

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_get",
        lambda hass: registry,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_entries_for_device",
        lambda _registry, _device_id: [mower_entry, ignored_entry],
    )

    conditions = await async_get_conditions(SimpleNamespace(), "device-123")

    assert conditions == [
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "is_mowing",
        },
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "is_docked",
        },
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "has_error",
        },
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "is_returning",
        },
    ]


def test_condition_from_config_matches_resolved_entity_state(monkeypatch) -> None:
    """Condition checker should resolve registry ids and inspect mower state."""
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_get",
        lambda hass: object(),
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_resolve_entity_id",
        lambda registry, entity_id: "lawn_mower.front_yard",
    )
    hass = SimpleNamespace(
        states=SimpleNamespace(
            get=lambda entity_id: SimpleNamespace(state=LawnMowerActivity.RETURNING)
            if entity_id == "lawn_mower.front_yard"
            else None
        )
    )

    checker = async_condition_from_config(
        hass,
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "1234567890abcdef1234567890abcdef",
            CONF_TYPE: "is_returning",
        },
    )

    assert checker(hass, {}) is True


def test_condition_from_config_rejects_non_matching_state(monkeypatch) -> None:
    """Condition checker should return false when the mower is in another state."""
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_get",
        lambda hass: object(),
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_condition.er.async_resolve_entity_id",
        lambda registry, entity_id: "lawn_mower.front_yard",
    )
    hass = SimpleNamespace(
        states=SimpleNamespace(
            get=lambda entity_id: SimpleNamespace(state=LawnMowerActivity.DOCKED)
        )
    )

    checker = async_condition_from_config(
        hass,
        {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "1234567890abcdef1234567890abcdef",
            CONF_TYPE: "has_error",
        },
    )

    assert checker(hass, {}) is False
