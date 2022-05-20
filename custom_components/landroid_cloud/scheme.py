"""Data schemes used by Landroid Cloud integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE

from .const import CLOUDS

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_TYPE, default=CLOUDS[0]): vol.In(CLOUDS),
    }
)
