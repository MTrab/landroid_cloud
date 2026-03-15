"""Command helpers for Landroid Cloud entities."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.exceptions import HomeAssistantError
from pyworxcloud.exceptions import APIException, NoConnectionError, OfflineError


async def async_run_cloud_command(command: Callable[[], Awaitable[object]]) -> None:
    """Run a pyworxcloud command and normalize errors for Home Assistant."""
    try:
        await command()
    except ValueError as err:
        message = str(err).strip() or "Invalid command data"
        raise HomeAssistantError(message) from err
    except (NoConnectionError, OfflineError) as err:
        raise HomeAssistantError("Mower is unavailable") from err
    except APIException as err:
        raise HomeAssistantError("Cloud command failed") from err
