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
        self._firmware_update_info: dict[str, dict[str, Any]] = {}

    async def async_setup(self) -> None:
        """Attach callbacks for push updates."""

        def _on_data_received(name: str, device: DeviceHandler) -> None:
            del name
            self._schedule_push_update(device)

        def _on_api_update(api_data: dict[str, Any]) -> None:
            del api_data
            self._schedule_api_refresh()

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
            self._sync_firmware_update_info(str(serial_number), device)
            self.async_set_updated_data(data)

    async def _refresh_from_cloud(self) -> None:
        """Refresh local state from cloud cache in a race-safe manner."""
        async with self._event_lock:
            data = _device_map(self.cloud)
            for serial_number, device in data.items():
                self._sync_firmware_update_info(serial_number, device)
            self.async_set_updated_data(data)

    def _schedule_push_update(self, device: DeviceHandler) -> None:
        """Schedule push update handling on Home Assistant's event loop."""
        try:
            self.hass.loop.call_soon_threadsafe(self._create_push_update_task, device)
        except RuntimeError:
            _LOGGER.debug("Ignoring push update scheduling after loop shutdown")

    def _schedule_api_refresh(self) -> None:
        """Schedule API refresh handling on Home Assistant's event loop."""
        try:
            self.hass.loop.call_soon_threadsafe(self._create_api_refresh_task)
        except RuntimeError:
            _LOGGER.debug("Ignoring API refresh scheduling after loop shutdown")

    def _create_push_update_task(self, device: DeviceHandler) -> None:
        """Create task for processing a push update."""
        self.hass.async_create_task(self._handle_push_update(device))

    def _create_api_refresh_task(self) -> None:
        """Create task for processing an API refresh event."""
        self.hass.async_create_task(self._refresh_from_cloud())

    async def _async_update_data(self) -> dict[str, DeviceHandler]:
        """Return current cloud cache without triggering device updates."""
        return _device_map(self.cloud)

    def firmware_update_info(self, serial_number: str) -> dict[str, Any]:
        """Return cached firmware update metadata for a mower."""
        return dict(self._firmware_update_info.get(serial_number, {}))

    def _sync_firmware_update_info(
        self, serial_number: str, device: DeviceHandler | None
    ) -> None:
        """Merge live firmware payload data into cached update metadata."""
        cached = self._firmware_update_info.get(serial_number)
        if cached is None or device is None:
            return

        firmware = getattr(device, "firmware", None)
        if not isinstance(firmware, dict):
            return

        merged = dict(cached)
        upgrade = firmware.get("upgrade")
        if isinstance(upgrade, dict):
            merged.update(upgrade)

        for source_key, target_key in (
            ("auto_upgrade", "auto_upgrade"),
            ("latest_version", "latest_version"),
            ("mandatory", "mandatory"),
            ("ota_supported", "ota_supported"),
            ("update_available", "update_available"),
            ("upgrade_failed", "upgrade_failed"),
            ("version", "current_version"),
        ):
            value = firmware.get(source_key)
            if value is not None:
                merged[target_key] = value

        self._firmware_update_info[serial_number] = merged

    async def async_refresh_firmware_update_info(
        self, serial_number: str
    ) -> dict[str, Any]:
        """Fetch and cache firmware update metadata for a mower."""
        info = await self.cloud.get_firmware_upgrade_info(serial_number)

        async with self._event_lock:
            device = (self.data or {}).get(serial_number)
            self._firmware_update_info[serial_number] = dict(info)
            self._sync_firmware_update_info(serial_number, device)
            cached = dict(self._firmware_update_info[serial_number])

        self.async_update_listeners()
        return cached

    async def async_get_firmware_update_info(
        self, serial_number: str
    ) -> dict[str, Any]:
        """Return cached firmware metadata, fetching it on first access."""
        if serial_number not in self._firmware_update_info:
            return await self.async_refresh_firmware_update_info(serial_number)
        return self.firmware_update_info(serial_number)
