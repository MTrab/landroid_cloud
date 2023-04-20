"""Get diagnostics."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_TYPE,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant

from .api import LandroidAPI
from .const import (
    ATTR_CLOUD,
    ATTR_DEVICEIDS,
    ATTR_DEVICES,
    ATTR_FEATUREBITS,
    DOMAIN,
    REDACT_TITLE,
)

TO_REDACT = {
    CONF_LONGITUDE,
    CONF_LATITUDE,
    CONF_UNIQUE_ID,
    CONF_PASSWORD,
    CONF_EMAIL,
    REDACT_TITLE,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data_entry = hass.data[DOMAIN][entry.entry_id]

    data_dict = {
        "entry": entry.as_dict(),
        ATTR_CLOUD: data_entry[ATTR_CLOUD],
        ATTR_DEVICEIDS: data_entry[ATTR_DEVICEIDS],
        ATTR_FEATUREBITS: data_entry[ATTR_FEATUREBITS],
        CONF_TYPE: data_entry[CONF_TYPE],
    }

    device_dict = {}
    for name, info in hass.data[DOMAIN][entry.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        device = {}
        for attr, value in api.device.__dict__.items():
            device.update({attr: value})

        device_dict.update({name: device})

    data_dict.update({"devices": device_dict})

    return async_redact_data(data_dict, TO_REDACT)
