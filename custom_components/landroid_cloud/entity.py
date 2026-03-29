"""Entity models for Landroid Cloud."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pyworxcloud import DeviceHandler

from .const import CONF_CLOUD, DOMAIN
from .coordinator import LandroidCloudCoordinator

T = TypeVar("T")


def _firmware_version(device: DeviceHandler) -> str:
    """Return firmware version from pyworxcloud device payload."""
    firmware = getattr(device, "firmware", None)
    if isinstance(firmware, dict):
        return str(firmware.get("version", "unknown"))
    if firmware is not None:
        return str(getattr(firmware, "version", "unknown"))
    return "unknown"


@dataclass(frozen=True, kw_only=True)
class LandroidEntityDescription[T]:
    """Generic entity description with value getter."""

    key: str
    value_fn: Callable[[DeviceHandler], T | None]


class LandroidBaseEntity(CoordinatorEntity[LandroidCloudCoordinator]):
    """Base class for all Landroid Cloud entities."""

    _attr_has_entity_name = True
    _attr_requires_online = False
    _attr_requires_auto_schedule = False

    def __init__(
        self,
        coordinator: LandroidCloudCoordinator,
        config_entry: ConfigEntry,
        serial_number: str,
        entity_key: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_{entity_key}"

    @property
    def device(self) -> DeviceHandler:
        """Return underlying device from coordinator data."""
        return self.coordinator.data[self._serial_number]

    @property
    def available(self) -> bool:
        """Return availability for the entity."""
        if not super().available:
            return False
        if self._serial_number not in self.coordinator.data:
            return False
        if self._attr_requires_auto_schedule and not auto_schedule_enabled(self.device):
            return False
        if self._attr_requires_online:
            return bool(getattr(self.device, "online", False))
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return Home Assistant device info."""
        device = self.device
        cloud_type = self._config_entry.data[CONF_CLOUD]

        info = {
            "identifiers": {(DOMAIN, str(device.serial_number))},
            "serial_number": str(device.serial_number),
            "name": str(device.name),
            "manufacturer": cloud_type.capitalize(),
            "model": str(getattr(device, "model", "Unknown")),
            "sw_version": _firmware_version(device),
            "suggested_area": self._config_entry.data[CONF_EMAIL],
        }

        mac_address = getattr(device, "mac_address", None)
        if mac_address and mac_address != "__UUID__":
            info["connections"] = {(CONNECTION_NETWORK_MAC, mac_address)}

        return DeviceInfo(**info)


def auto_schedule(device: DeviceHandler) -> dict:
    """Return the normalized auto-schedule block when available."""
    schedules = getattr(device, "schedules", None)
    if not isinstance(schedules, dict):
        return {}
    value = schedules.get("auto_schedule")
    return value if isinstance(value, dict) else {}


def auto_schedule_settings(device: DeviceHandler) -> dict:
    """Return normalized auto-schedule settings when available."""
    value = auto_schedule(device).get("settings")
    return value if isinstance(value, dict) else {}


def auto_schedule_enabled(device: DeviceHandler) -> bool:
    """Return whether auto-schedule is enabled for the device."""
    return bool(auto_schedule(device).get("enabled", False))
