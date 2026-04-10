"""Diagnostics support for Landroid Cloud."""

from __future__ import annotations

from datetime import date, datetime
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
    "mqtt_topics",
    "mqtt_endpoint",
    "mac",
    "mac_address",
    "uuid",
}


def _capabilities_value(device: Any) -> int | None:
    """Return a stable integer representation of device capabilities."""
    capabilities = getattr(device, "capabilities", None)
    if capabilities is None:
        return None

    if isinstance(capabilities, int):
        return capabilities

    raw_int = getattr(capabilities, "__int__", None)
    if isinstance(raw_int, int):
        return raw_int
    if callable(raw_int):
        try:
            return int(raw_int())
        except TypeError, ValueError:
            return None

    try:
        return int(capabilities)
    except TypeError, ValueError:
        return None


def _jsonable(value: Any) -> Any:
    """Convert diagnostics payloads to JSON-friendly structures."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]

    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, str | int | float | bool) or value is None:
        return value

    if hasattr(value, "as_dict"):
        as_dict = value.as_dict()
        if isinstance(as_dict, dict):
            return _jsonable(as_dict)

    return str(value)


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
            "firmware": _jsonable(dict(getattr(device, "firmware", {}))),
            "online": getattr(device, "online", None),
            "capabilities": _capabilities_value(device),
            "status": _jsonable(dict(getattr(device, "status", {}))),
            "error": _jsonable(dict(getattr(device, "error", {}))),
            "zone": _jsonable(dict(getattr(device, "zone", {}))),
            "schedules": _jsonable(dict(getattr(device, "schedules", {}))),
            "last_status": _jsonable(getattr(device, "last_status", None)),
            "raw_cfg": _jsonable(getattr(device, "raw_cfg", None)),
            "raw_dat": _jsonable(getattr(device, "raw_dat", None)),
            "json_data": _jsonable(getattr(device, "json_data", None)),
            "mower": _jsonable(getattr(device, "mower", None)),
        }

    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "domain": DOMAIN,
            "devices": devices,
        },
        TO_REDACT,
    )
