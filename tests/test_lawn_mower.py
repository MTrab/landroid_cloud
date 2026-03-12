"""Tests for mower activity mapping."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.components.lawn_mower import LawnMowerActivity
import pytest

from custom_components.landroid_cloud.lawn_mower import (
    STATUS_ACTIVITY_MAP,
    LandroidCloudMowerEntity,
)


def test_start_sequence_states_map_to_mowing() -> None:
    """Start-sequence related status codes should map to standard mowing state."""
    assert STATUS_ACTIVITY_MAP[2] is LawnMowerActivity.MOWING
    assert STATUS_ACTIVITY_MAP[3] is LawnMowerActivity.MOWING


def test_unknown_state_defaults_to_error() -> None:
    """Unknown status ids should not map to non-standard activities."""
    assert (
        STATUS_ACTIVITY_MAP.get(999, LawnMowerActivity.ERROR) is LawnMowerActivity.ERROR
    )


@pytest.mark.asyncio
async def test_ots_service_calls_cloud_ots() -> None:
    """OTS service should call the cloud command with legacy arguments."""
    entity = object.__new__(LandroidCloudMowerEntity)
    entity._serial_number = "serial"
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(ots=AsyncMock()),
        data={"serial": SimpleNamespace(serial_number="serial")},
    )

    await entity._async_service_ots(boundary=True, runtime=45)

    entity.coordinator.cloud.ots.assert_awaited_once_with("serial", True, 45)
