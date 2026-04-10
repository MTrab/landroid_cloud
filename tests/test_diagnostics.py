"""Tests for diagnostics payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from custom_components.landroid_cloud.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.mark.asyncio
async def test_diagnostics_include_raw_device_data_and_redact_secrets() -> None:
    """Diagnostics should expose raw device payloads while redacting secrets."""
    device = SimpleNamespace(
        name="Garden",
        model="WR147E",
        firmware={"version": "3.32"},
        online=True,
        capabilities=0,
        status={"id": 7},
        error={"id": 0},
        zone={"current": 1},
        schedules={"active": True},
        last_status={
            "timestamp": datetime(2026, 4, 10, 12, 30, tzinfo=UTC),
            "payload": {
                "cfg": {"sn": "SN123", "modules": {"US": {"enabled": 1}}},
                "dat": {"mac": "AA:BB:CC:DD:EE:FF", "uuid": "uuid-123"},
            },
        },
        raw_cfg={"sn": "SN123", "mqtt_topics": {"command_in": "topic/in"}},
        raw_dat={"mac": "AA:BB:CC:DD:EE:FF", "uuid": "uuid-123", "rsi": -67},
        json_data={"cfg": {"sn": "SN123"}, "dat": {"mac": "AA:BB:CC:DD:EE:FF"}},
        mower={
            "serial_number": "SN123",
            "mqtt_endpoint": "mqtt.example.invalid",
            "user_id": "user-123",
            "last_status": {"payload": {"cfg": {"sn": "SN123"}}},
        },
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(
            coordinator=SimpleNamespace(data={"SN123": device})
        ),
        as_dict=lambda: {
            "data": {
                "email": "user@example.com",
                "password": "super-secret",
                "access_token": "access-123",
                "refresh_token": "refresh-123",
            }
        },
    )

    result = await async_get_config_entry_diagnostics(SimpleNamespace(), entry)

    assert result["entry"]["data"]["email"] == "**REDACTED**"
    assert result["entry"]["data"]["password"] == "**REDACTED**"
    assert result["entry"]["data"]["access_token"] == "**REDACTED**"
    assert result["entry"]["data"]["refresh_token"] == "**REDACTED**"
    assert result["devices"]["SN123"]["raw_cfg"]["sn"] == "SN123"
    assert result["devices"]["SN123"]["raw_cfg"]["mqtt_topics"] == "**REDACTED**"
    assert result["devices"]["SN123"]["raw_dat"]["rsi"] == -67
    assert result["devices"]["SN123"]["raw_dat"]["mac"] == "**REDACTED**"
    assert result["devices"]["SN123"]["raw_dat"]["uuid"] == "**REDACTED**"
    assert result["devices"]["SN123"]["json_data"]["dat"]["mac"] == "**REDACTED**"
    assert result["devices"]["SN123"]["mower"]["mqtt_endpoint"] == "**REDACTED**"
    assert result["devices"]["SN123"]["mower"]["user_id"] == "**REDACTED**"
    assert result["devices"]["SN123"]["capabilities"] == 0
    assert result["devices"]["SN123"]["last_status"]["timestamp"] == (
        "2026-04-10T12:30:00+00:00"
    )


@pytest.mark.asyncio
async def test_diagnostics_handle_capability_objects() -> None:
    """Diagnostics should serialize pyworxcloud Capability objects safely."""

    class _Capability:
        __int__ = 12

    device = SimpleNamespace(
        name="Garden",
        model="WR147E",
        firmware={},
        online=True,
        capabilities=_Capability(),
        status={},
        error={},
        zone={},
        schedules={},
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(
            coordinator=SimpleNamespace(data={"SN123": device})
        ),
        as_dict=lambda: {"data": {}},
    )

    result = await async_get_config_entry_diagnostics(SimpleNamespace(), entry)

    assert result["devices"]["SN123"]["capabilities"] == 12
