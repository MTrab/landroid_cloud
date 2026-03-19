"""The Landroid Cloud integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.loader import async_get_integration
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
from .const import (
    CloudProvider,
    CONF_CLOUD,
    CONF_COMMAND_TIMEOUT,
    DEFAULT_CLOUD,
    DEFAULT_COMMAND_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    STARTUP,
)
from .coordinator import LandroidCloudCoordinator
from .models import LandroidRuntimeData

type LandroidConfigEntry = ConfigEntry[LandroidRuntimeData]
_LOGGER = logging.getLogger(__name__)
_CONFIG_ENTRY_VERSION = 2
_SUPPORTED_CLOUDS = {provider.value for provider in CloudProvider}


def _normalize_cloud_provider(value: Any | None) -> str:
    """Return a canonical cloud provider value."""
    if isinstance(value, str):
        cloud = value.lower()
        if cloud in _SUPPORTED_CLOUDS:
            return cloud

    return DEFAULT_CLOUD


def _entry_cloud_provider(entry: ConfigEntry[Any]) -> str:
    """Resolve the configured cloud provider from current or legacy data."""
    return _normalize_cloud_provider(
        entry.data.get(CONF_CLOUD) or entry.data.get(CONF_TYPE)
    )


def _target_unique_id(email: str, cloud: str) -> str:
    """Return the canonical v7 unique id."""
    return f"{email.lower()}::{cloud}"


def _legacy_unique_id_candidates(
    email: str, cloud: str, legacy_cloud: str | None
) -> set[str]:
    """Return known v6 unique id candidates for an entry."""
    candidates = {
        f"{email}_{cloud}",
        f"{email.lower()}_{cloud.lower()}",
    }
    if legacy_cloud is not None:
        candidates.update(
            {
                f"{email}_{legacy_cloud}",
                f"{email.lower()}_{legacy_cloud.lower()}",
            }
        )

    return candidates


def _unique_id_conflicts(
    hass: HomeAssistant, entry: ConfigEntry[Any], unique_id: str
) -> bool:
    """Return whether another config entry already uses the target unique id."""
    for other_entry in hass.config_entries.async_entries(DOMAIN):
        if other_entry.entry_id != entry.entry_id and other_entry.unique_id == unique_id:
            return True

    return False


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry[Any]) -> bool:
    """Migrate an older config entry to the v7 schema."""
    if entry.version >= _CONFIG_ENTRY_VERSION:
        return True

    original_data = dict(entry.data)
    migrated_data = dict(original_data)
    cloud = _entry_cloud_provider(entry)

    if migrated_data.get(CONF_CLOUD) != cloud:
        migrated_data[CONF_CLOUD] = cloud

    migrated_data.pop(CONF_TYPE, None)

    update_kwargs: dict[str, Any] = {
        "data": migrated_data,
        "version": _CONFIG_ENTRY_VERSION,
    }

    email = migrated_data.get(CONF_EMAIL)
    if isinstance(email, str) and email:
        target_unique_id = _target_unique_id(email, cloud)
        current_unique_id = entry.unique_id
        legacy_cloud = original_data.get(CONF_TYPE)
        legacy_candidates = {
            candidate.casefold()
            for candidate in _legacy_unique_id_candidates(
                email, cloud, legacy_cloud if isinstance(legacy_cloud, str) else None
            )
        }

        if current_unique_id != target_unique_id:
            if current_unique_id is None or current_unique_id.casefold() in legacy_candidates:
                if _unique_id_conflicts(hass, entry, target_unique_id):
                    _LOGGER.warning(
                        "Skipping unique_id migration for entry %s because %s is already in use",
                        entry.entry_id,
                        target_unique_id,
                    )
                else:
                    update_kwargs["unique_id"] = target_unique_id

    hass.config_entries.async_update_entry(entry, **update_kwargs)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: LandroidConfigEntry) -> bool:
    """Set up Landroid Cloud from a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    cloud_type = _entry_cloud_provider(entry)
    cloud = WorxCloud(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        cloud_type,
        tz=hass.config.time_zone,
        command_timeout=entry.options.get(
            CONF_COMMAND_TIMEOUT, DEFAULT_COMMAND_TIMEOUT
        ),
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
    except (
        NoConnectionError,
        ServiceUnavailableError,
        InternalServerError,
        TimeoutError,
    ) as err:
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
