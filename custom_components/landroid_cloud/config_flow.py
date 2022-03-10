"""Config flow for Worx Landroid Cloud."""
import logging

import requests.exceptions
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
from pyworxcloud import WorxCloud

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE, CONF_UNIQUE_ID
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    worx = WorxCloud()
    auth = await hass.async_add_executor_job(
        worx.initialize, data[CONF_EMAIL], data[CONF_PASSWORD], data[CONF_TYPE]
    )
    if not auth:
        raise InvalidAuth

    return {"title": f"Worx Landroid Cloud"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Worx Landroid Cloud."""

    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                validated = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                return self.async_create_entry(
                    title=validated["title"], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
