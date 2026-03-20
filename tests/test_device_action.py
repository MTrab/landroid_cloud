"""Tests for Landroid Cloud device actions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.components.lawn_mower import LawnMowerEntityFeature
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
import pytest

from custom_components.landroid_cloud import DOMAIN
from custom_components.landroid_cloud.device_action import (
    async_call_action_from_config,
    async_get_actions,
    async_validate_action_config,
)


@pytest.mark.asyncio
async def test_get_actions_returns_supported_mower_actions(monkeypatch) -> None:
    """Device actions should expose supported mower commands only."""
    registry = object()
    mower_entry = SimpleNamespace(
        domain="lawn_mower",
        platform=DOMAIN,
        id="registry-entry-id",
        entity_id="lawn_mower.front_yard",
    )
    ignored_wrong_platform = SimpleNamespace(
        domain="lawn_mower",
        platform="other_integration",
        id="other-entry",
        entity_id="lawn_mower.other",
    )
    ignored_wrong_domain = SimpleNamespace(
        domain="sensor",
        platform=DOMAIN,
        id="sensor-entry",
        entity_id="sensor.front_yard_status",
    )

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_action.er.async_get",
        lambda hass: registry,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_action.er.async_entries_for_device",
        lambda _registry, _device_id: [
            mower_entry,
            ignored_wrong_platform,
            ignored_wrong_domain,
        ],
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_action.get_supported_features",
        lambda hass, entity_id: LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.DOCK
        if entity_id == mower_entry.entity_id
        else LawnMowerEntityFeature(0),
    )

    actions = await async_get_actions(SimpleNamespace(), "device-123")

    assert actions == [
        {
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "start_mowing",
        },
        {
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "dock",
        },
    ]


@pytest.mark.asyncio
async def test_validate_action_config_resolves_registry_entry(monkeypatch) -> None:
    """Validation should resolve entity registry ids to entity ids."""
    registry_entry_id = "1234567890abcdef1234567890abcdef"

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_action.er.async_get",
        lambda hass: object(),
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_action.er.async_resolve_entity_id",
        lambda registry, entity_id: "lawn_mower.front_yard"
        if entity_id == registry_entry_id
        else entity_id,
    )

    validated = await async_validate_action_config(
        SimpleNamespace(),
        {
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: registry_entry_id,
            CONF_TYPE: "pause",
        },
    )

    assert validated == {
        CONF_DEVICE_ID: "device-123",
        CONF_DOMAIN: DOMAIN,
        CONF_ENTITY_ID: "lawn_mower.front_yard",
        CONF_TYPE: "pause",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action_type", "service"),
    [
        ("start_mowing", "start_mowing"),
        ("pause", "pause"),
        ("dock", "dock"),
    ],
)
async def test_call_action_from_config_calls_lawn_mower_service(
    action_type: str, service: str
) -> None:
    """Executing a device action should call the standard mower service."""
    hass = SimpleNamespace(services=SimpleNamespace(async_call=AsyncMock()))

    await async_call_action_from_config(
        hass,
        {
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "lawn_mower.front_yard",
            CONF_TYPE: action_type,
        },
        variables={},
        context=None,
    )

    hass.services.async_call.assert_awaited_once_with(
        "lawn_mower",
        service,
        {ATTR_ENTITY_ID: "lawn_mower.front_yard"},
        blocking=True,
        context=None,
    )
