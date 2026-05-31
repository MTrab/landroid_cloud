"""Command helpers for Landroid Cloud entities."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.exceptions import HomeAssistantError
from pyworxcloud.exceptions import APIException, NoConnectionError, OfflineError

MQTT_NOT_READY_ERROR = "MQTT connection is not ready"
MQTT_NOT_READY_MESSAGE = (
    "MQTT is not connected. Wait for Landroid Cloud to reconnect, then try again."
)


def is_mqtt_connection_not_ready(err: BaseException) -> bool:
    """Return whether pyworxcloud rejected a command because MQTT is disconnected."""
    return isinstance(err, NoConnectionError) and MQTT_NOT_READY_ERROR in str(err)


def cloud_connection_error_message(err: BaseException) -> str:
    """Return a user-facing message for cloud connection command failures."""
    if is_mqtt_connection_not_ready(err):
        return MQTT_NOT_READY_MESSAGE
    return "Mower is unavailable"


async def async_run_cloud_command(command: Callable[[], Awaitable[object]]) -> None:
    """Run a pyworxcloud command and normalize errors for Home Assistant."""
    try:
        await command()
    except ValueError as err:
        message = str(err).strip() or "Invalid command data"
        raise HomeAssistantError(message) from err
    except (NoConnectionError, OfflineError) as err:
        raise HomeAssistantError(cloud_connection_error_message(err)) from err
    except APIException as err:
        raise HomeAssistantError("Cloud command failed") from err
