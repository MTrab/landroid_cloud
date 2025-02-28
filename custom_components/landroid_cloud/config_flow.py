"""Adds support for Landroid Cloud compatible devices."""

from __future__ import annotations

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from pyworxcloud import WorxCloud
from pyworxcloud.exceptions import AuthorizationError, TooManyRequestsError

from .const import DOMAIN, LOGLEVEL
from .scheme import DATA_SCHEMA
from .utils.logger import LandroidLogger, LoggerType, LogLevel

LOGGER = LandroidLogger(name=__name__, log_level=LOGLEVEL)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    LOGGER.log(LoggerType.CONFIG, "data: %s", data)

    worx = WorxCloud(
        data.get(CONF_EMAIL), data.get(CONF_PASSWORD), data.get(CONF_TYPE).lower()
    )
    try:
        auth = await hass.async_add_executor_job(worx.authenticate)
    except TooManyRequestsError:
        raise TooManyRequests from None
    except AuthorizationError:
        raise InvalidAuth from None

    if not auth:
        raise InvalidAuth

    return {"title": f"{data[CONF_TYPE]} - {data[CONF_EMAIL]}"}


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class TooManyRequests(exceptions.HomeAssistantError):
    """Error to indicate we made too many requests."""


class LandroidCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Landroid Cloud."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def check_for_existing(self, data):
        """Check whether an existing entry is using the same URLs."""
        return any(
            entry.data.get(CONF_EMAIL) == data.get(CONF_EMAIL)
            and entry.data.get(CONF_TYPE).lower()
            == (
                data.get(CONF_TYPE).lower()
                if not isinstance(data.get(CONF_TYPE), type(None))
                else "worx"
            )
            for entry in self._async_current_entries()
        )

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial Landroid Cloud step."""
        self._errors = {}
        if user_input is not None:
            if self.check_for_existing(user_input):
                return self.async_abort(reason="already_exists")

            try:
                validated = await validate_input(self.hass, user_input)
            except CannotConnect:
                self._errors["base"] = "cannot_connect"
            except InvalidAuth:
                self._errors["base"] = "invalid_auth"
            except TooManyRequests:
                self._errors["base"] = "too_many_requests"
            except Exception as ex:  # pylint: disable=broad-except
                LOGGER.log(
                    LoggerType.CONFIG,
                    "Unexpected exception: %s",
                    ex,
                    log_level=LogLevel.ERROR,
                )
                self._errors["base"] = "unknown"

            if "base" not in self._errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_EMAIL]}_{user_input[CONF_TYPE]}"
                )

                return self.async_create_entry(
                    title=validated["title"],
                    data=user_input,
                    description=f"API connector for {validated['title']} cloud",
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=self._errors
        )

    async def async_step_import(self, import_config):
        """Import a config entry."""
        if import_config is not None:
            if self.check_for_existing(import_config):
                LOGGER.log(
                    LoggerType.CONFIG_IMPORT,
                    "Landroid_cloud configuration for %s already imported, you can "
                    "safely remove the entry from your configuration.yaml as this "
                    "is no longer used",
                    import_config.get(CONF_EMAIL),
                    log_level=LogLevel.WARNING,
                )
                return self.async_abort(reason="already_exists")

            try:
                await validate_input(self.hass, import_config)
            except CannotConnect:
                self._errors["base"] = "cannot_connect"
            except InvalidAuth:
                self._errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                LOGGER.log(
                    LoggerType.CONFIG_IMPORT,
                    "Unexpected exception",
                    log_level=LogLevel.ERROR,
                )
                self._errors["base"] = "unknown"

            if "base" not in self._errors:
                return self.async_create_entry(
                    title=f"Import - {import_config.get(CONF_EMAIL)}",
                    data=import_config,
                )
