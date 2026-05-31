"""Tests for cloud command error handling."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from pyworxcloud.exceptions import APIException, NoConnectionError, OfflineError

from custom_components.landroid_cloud.commands import async_run_cloud_command


@pytest.mark.asyncio
async def test_async_run_cloud_command_maps_mqtt_not_ready() -> None:
    """MQTT disconnects should surface an actionable Home Assistant error."""
    command = AsyncMock(side_effect=NoConnectionError("MQTT connection is not ready"))

    with pytest.raises(
        HomeAssistantError,
        match="MQTT is not connected",
    ):
        await async_run_cloud_command(command)


@pytest.mark.asyncio
async def test_async_run_cloud_command_maps_offline_errors() -> None:
    """Generic availability errors should keep the existing unavailable message."""
    command = AsyncMock(side_effect=OfflineError("offline"))

    with pytest.raises(HomeAssistantError, match="Mower is unavailable"):
        await async_run_cloud_command(command)


@pytest.mark.asyncio
async def test_async_run_cloud_command_maps_api_errors() -> None:
    """API failures should keep the existing cloud command message."""
    command = AsyncMock(side_effect=APIException("api failed"))

    with pytest.raises(HomeAssistantError, match="Cloud command failed"):
        await async_run_cloud_command(command)
