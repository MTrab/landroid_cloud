"""Data coordinator for Landroid Cloud."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyworxcloud import DeviceHandler, LandroidEvent, WorxCloud

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _device_map(cloud: WorxCloud) -> dict[str, DeviceHandler]:
    """Build a serial-indexed map of devices from cloud state."""
    return {
        str(device.serial_number): device
        for device in cloud.devices.values()
        if getattr(device, "serial_number", None) is not None
    }


class LandroidCloudCoordinator(DataUpdateCoordinator[dict[str, DeviceHandler]]):
    """Coordinate state updates for cloud-connected mowers."""

    def __init__(self, hass: HomeAssistant, cloud: WorxCloud) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )
        self.cloud = cloud
        self._event_lock = asyncio.Lock()

    async def async_setup(self) -> None:
        """Attach callbacks for push updates."""

        async def _on_data_received(name: str, device: DeviceHandler) -> None:
            del name
            await self._handle_push_update(device)

        async def _on_api_update(api_data: dict[str, Any]) -> None:
            del api_data
            await self._refresh_from_cloud()

        self.cloud.set_callback(LandroidEvent.DATA_RECEIVED, _on_data_received)
        self.cloud.set_callback(LandroidEvent.API, _on_api_update)

    async def async_shutdown(self) -> None:
        """Detach callbacks for push updates."""
        # pyworxcloud exposes callback registration, but not explicit unregistration.
        # Reset handlers to no-op before cloud disconnect to avoid stale callbacks.
        self.cloud.set_callback(LandroidEvent.DATA_RECEIVED, lambda **_: None)
        self.cloud.set_callback(LandroidEvent.API, lambda **_: None)

    async def _handle_push_update(self, device: DeviceHandler) -> None:
        """Merge push update into coordinator data in a race-safe manner."""
        serial_number = getattr(device, "serial_number", None)
        if serial_number is None:
            return

        async with self._event_lock:
            data = dict(self.data) if self.data else {}
            data[str(serial_number)] = device
            self.async_set_updated_data(data)

    async def _refresh_from_cloud(self) -> None:
        """Refresh local state from cloud cache in a race-safe manner."""
        async with self._event_lock:
            self.async_set_updated_data(_device_map(self.cloud))

    async def _async_update_data(self) -> dict[str, DeviceHandler]:
        """Return current cloud cache without triggering device updates."""
        return _device_map(self.cloud)
