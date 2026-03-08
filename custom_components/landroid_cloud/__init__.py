"""The Landroid Cloud integration."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
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

from .awsiot import async_prime_awsiot_metrics
from .const import CONF_CLOUD, CONF_COMMAND_TIMEOUT, DEFAULT_COMMAND_TIMEOUT, DOMAIN, PLATFORMS
from .coordinator import LandroidCloudCoordinator
from .models import LandroidRuntimeData

type LandroidConfigEntry = ConfigEntry[LandroidRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: LandroidConfigEntry) -> bool:
    """Set up Landroid Cloud from a config entry."""
    cloud = WorxCloud(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_CLOUD],
        tz=hass.config.time_zone,
        command_timeout=entry.options.get(CONF_COMMAND_TIMEOUT, DEFAULT_COMMAND_TIMEOUT),
    )

    try:
        await cloud.authenticate()
        await async_prime_awsiot_metrics()
        connected = await asyncio.wait_for(cloud.connect(), timeout=30)
    except AuthorizationError as err:
        raise ConfigEntryAuthFailed("Invalid credentials") from err
    except (RequestError, ForbiddenError, NotFoundError) as err:
        raise ConfigEntryNotReady("Cloud endpoint rejected setup request") from err
    except TooManyRequestsError as err:
        raise ConfigEntryNotReady("Too many requests to cloud API") from err
    except (NoConnectionError, ServiceUnavailableError, InternalServerError, TimeoutError) as err:
        raise ConfigEntryNotReady("Cloud service unavailable") from err
    except APIException as err:
        raise ConfigEntryNotReady("Unexpected API error") from err

    if not connected:
        await cloud.disconnect()
        raise ConfigEntryNotReady("No mowers found for this account")

    coordinator = LandroidCloudCoordinator(hass, cloud)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = LandroidRuntimeData(cloud=cloud, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: LandroidConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    runtime_data = entry.runtime_data
    await runtime_data.coordinator.async_shutdown()
    await runtime_data.cloud.disconnect()

    return True


async def async_reload_entry(hass: HomeAssistant, entry: LandroidConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
