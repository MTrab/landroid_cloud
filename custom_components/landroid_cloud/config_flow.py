"""Config flow for Landroid Cloud."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pyworxcloud import WorxCloud
from pyworxcloud.exceptions import (
    APIException,
    AuthorizationError,
    ForbiddenError,
    InternalServerError,
    NoConnectionError,
    NotFoundError,
    RequestError,
    ServiceUnavailableError,
    TooManyRequestsError,
)

from .const import (
    CONF_CLOUD,
    CONF_COMMAND_TIMEOUT,
    DEFAULT_CLOUD,
    DEFAULT_COMMAND_TIMEOUT,
    DOMAIN,
    MAX_COMMAND_TIMEOUT,
    MIN_COMMAND_TIMEOUT,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CLOUD, default=DEFAULT_CLOUD): vol.In(
            ["worx", "kress", "landxcape"]
        ),
    }
)


async def _validate_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    cloud = WorxCloud(
        user_input[CONF_EMAIL],
        user_input[CONF_PASSWORD],
        user_input[CONF_CLOUD],
    )

    try:
        await cloud.authenticate()
        await async_prime_awsiot_metrics()
        connected = await asyncio.wait_for(cloud.connect(), timeout=30)
        if not connected:
            return {"title": user_input[CONF_EMAIL], "device_count": 0}

        return {
            "title": f"{user_input[CONF_EMAIL]} ({user_input[CONF_CLOUD]})",
            "device_count": len(cloud.devices),
        }
    finally:
        await cloud.disconnect()


class LandroidCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Landroid Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input[CONF_EMAIL].lower()}::{user_input[CONF_CLOUD]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                info = await _validate_input(user_input)
            except AuthorizationError:
                errors["base"] = "invalid_auth"
            except TooManyRequestsError:
                errors["base"] = "too_many_requests"
            except (NoConnectionError, ServiceUnavailableError):
                errors["base"] = "cannot_connect"
            except (RequestError, ForbiddenError, NotFoundError, InternalServerError):
                errors["base"] = "api_error"
            except APIException:
                errors["base"] = "unknown"
            except TimeoutError:
                errors["base"] = "timeout"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return LandroidCloudOptionsFlow(config_entry)


class LandroidCloudOptionsFlow(OptionsFlow):
    """Handle Landroid Cloud options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(
            CONF_COMMAND_TIMEOUT, DEFAULT_COMMAND_TIMEOUT
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COMMAND_TIMEOUT, default=current): vol.All(
                        vol.Coerce(float),
                        vol.Range(
                            min=MIN_COMMAND_TIMEOUT,
                            max=MAX_COMMAND_TIMEOUT,
                        ),
                    )
                }
            ),
        )
