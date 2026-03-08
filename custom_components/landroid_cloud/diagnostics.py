"""Diagnostics support for Landroid Cloud."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "email",
    "password",
    "access_token",
    "refresh_token",
    "user_id",
    "mqtt_endpoint",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    del hass
    runtime_data = entry.runtime_data

    devices = {}
    for serial_number, device in runtime_data.coordinator.data.items():
        devices[serial_number] = {
            "name": getattr(device, "name", None),
            "model": getattr(device, "model", None),
            "firmware": dict(getattr(device, "firmware", {})),
            "online": getattr(device, "online", None),
            "capabilities": int(getattr(device.capabilities, "__int__", 0)),
            "status": dict(getattr(device, "status", {})),
            "error": dict(getattr(device, "error", {})),
            "zone": dict(getattr(device, "zone", {})),
            "schedules": dict(getattr(device, "schedules", {})),
        }

    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "domain": DOMAIN,
            "devices": devices,
        },
        TO_REDACT,
    )
