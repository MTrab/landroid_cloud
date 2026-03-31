"""Tests for Landroid Cloud device triggers."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest
from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_FOR,
    CONF_PLATFORM,
    CONF_TYPE,
)

from custom_components.landroid_cloud import DOMAIN
from custom_components.landroid_cloud.const import MOWER_STATE_SEARCHING_ZONE
from custom_components.landroid_cloud.device_trigger import (
    async_attach_trigger,
    async_get_trigger_capabilities,
    async_get_triggers,
)


@pytest.mark.asyncio
async def test_get_triggers_returns_supported_mower_triggers(monkeypatch) -> None:
    """Device triggers should be exposed for mower entities only."""
    registry = object()
    mower_entry = SimpleNamespace(
        domain="lawn_mower",
        platform=DOMAIN,
        id="registry-entry-id",
        entity_id="lawn_mower.front_yard",
    )
    ignored_entry = SimpleNamespace(
        domain="sensor",
        platform=DOMAIN,
        id="sensor-entry",
        entity_id="sensor.front_yard_status",
    )

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.er.async_get",
        lambda hass: registry,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.er.async_entries_for_device",
        lambda _registry, _device_id: [mower_entry, ignored_entry],
    )

    triggers = await async_get_triggers(SimpleNamespace(), "device-123")

    assert triggers == [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "mowing",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "docked",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "error",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "returning",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "edgecut",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "starting",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "zoning",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "searching_zone",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "idle",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "rain_delayed",
        },
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "registry-entry-id",
            CONF_TYPE: "escaped_digital_fence",
        },
    ]


@pytest.mark.asyncio
async def test_get_trigger_capabilities_supports_for() -> None:
    """Trigger capabilities should expose the optional duration field."""
    capabilities = await async_get_trigger_capabilities(SimpleNamespace(), {})
    schema = capabilities["extra_fields"]
    validated = schema({CONF_FOR: {"minutes": 5}})

    assert validated == {CONF_FOR: timedelta(minutes=5)}


@pytest.mark.asyncio
async def test_attach_trigger_builds_state_trigger(monkeypatch) -> None:
    """Trigger attachment should delegate to a state trigger with mower state."""
    validated_config: dict | None = None

    async def _validate(_hass, config):
        nonlocal validated_config
        validated_config = config
        return config

    async def _attach(_hass, config, action, trigger_info, platform_type):
        assert action == "callback"
        assert trigger_info == "info"
        assert platform_type == "device"
        return "remove-callback"

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.state_trigger.async_validate_trigger_config",
        _validate,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.state_trigger.async_attach_trigger",
        _attach,
    )

    result = await async_attach_trigger(
        SimpleNamespace(),
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "lawn_mower.front_yard",
            CONF_TYPE: "returning",
            CONF_FOR: {"minutes": 1},
        },
        action="callback",
        trigger_info="info",
    )

    assert result == "remove-callback"
    assert validated_config == {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: "lawn_mower.front_yard",
        "to": LawnMowerActivity.RETURNING,
        CONF_FOR: {"minutes": 1},
    }


@pytest.mark.asyncio
async def test_attach_trigger_supports_restored_legacy_states(monkeypatch) -> None:
    """Trigger attachment should also work for restored legacy mower states."""
    validated_config: dict | None = None

    async def _validate(_hass, config):
        nonlocal validated_config
        validated_config = config
        return config

    async def _attach(_hass, config, action, trigger_info, platform_type):
        return "remove-callback"

    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.state_trigger.async_validate_trigger_config",
        _validate,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.device_trigger.state_trigger.async_attach_trigger",
        _attach,
    )

    await async_attach_trigger(
        SimpleNamespace(),
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "device-123",
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: "lawn_mower.front_yard",
            CONF_TYPE: "searching_zone",
        },
        action="callback",
        trigger_info="info",
    )

    assert validated_config == {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: "lawn_mower.front_yard",
        "to": MOWER_STATE_SEARCHING_ZONE,
    }
