"""Adds support for Landroid Cloud compatible devices."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.loader import async_get_integration
from pyworxcloud import WorxCloud, exceptions
import requests

from .api import LandroidAPI
from .const import (
    ATTR_API,
    ATTR_CLOUD,
    ATTR_DEVICE,
    ATTR_DEVICEIDS,
    ATTR_DEVICES,
    ATTR_FEATUREBITS,
    DOMAIN,
    LOGLEVEL,
    PLATFORMS_PRIMARY,
    PLATFORMS_SECONDARY,
    STARTUP,
)
from .services import async_setup_services
from .utils.logger import LandroidLogger, LoggerType, LogLevel

LOGGER = LandroidLogger(name=__name__, log_level=LOGLEVEL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up cloud API connector from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await check_unique_id(hass, entry)
    result = await _async_setup(hass, entry)

    if result:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_PRIMARY)

    await async_setup_services(hass)

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS_PRIMARY + PLATFORMS_SECONDARY
    )

    services = []
    if unload_ok:
        await hass.async_add_executor_job(
            hass.data[DOMAIN][entry.entry_id][ATTR_CLOUD].disconnect
        )

        hass.data[DOMAIN].pop(entry.entry_id)

        if not hass.data[DOMAIN]:
            for service in services:
                hass.services.async_remove(DOMAIN, service)

        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle setup of the integration, using a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    LOGGER.log(
        None,
        STARTUP,
        integration.version,
        log_level=LogLevel.INFO,
    )

    cloud_email = entry.data.get(CONF_EMAIL)
    cloud_password = entry.data.get(CONF_PASSWORD)
    cloud_type = entry.data.get(CONF_TYPE)

    if cloud_type is None:
        cloud_type = "worx"

    LOGGER.log(
        LoggerType.SETUP,
        "Opening connection to %s account for %s",
        cloud_type,
        cloud_email,
    )
    cloud = WorxCloud(
        cloud_email, cloud_password, cloud_type.lower(), tz=hass.config.time_zone
    )
    auth = False

    try:
        auth = await hass.async_add_executor_job(cloud.authenticate)
    except exceptions.RequestError:
        raise ConfigEntryNotReady(f"Request for {cloud_email} was malformed.")
    except exceptions.AuthorizationError:
        raise ConfigEntryNotReady("Unauthorized - please check your credentials")
    except exceptions.ForbiddenError:
        raise ConfigEntryNotReady(f"Server rejected access for {cloud_email}")
    except exceptions.NotFoundError:
        raise ConfigEntryNotReady("No API endpoint was found")
    except exceptions.TooManyRequestsError:
        raise ConfigEntryNotReady(
            f"Too many requests for {cloud_email} - IP address temporary banned."
        )
    except exceptions.InternalServerError:
        raise ConfigEntryNotReady(
            f"Internal server error happend for the request to {cloud_email}"
        )
    except exceptions.ServiceUnavailableError:
        raise ConfigEntryNotReady("Cloud service unavailable")
    except exceptions.APIException as ex:
        raise ConfigEntryNotReady("Error connecting to the API") from ex

    if not auth:
        raise ConfigEntryNotReady(f"Authentication error for {cloud_email}")

    try:
        async with asyncio.timeout(30):
            await hass.async_add_executor_job(cloud.connect)

        # while not cloud.mqtt.connected:
        #     await asyncio.sleep(0.1)
    except TimeoutError:
        try:
            await hass.async_add_executor_job(cloud.disconnect)
            raise ConfigEntryNotReady(f"Timed out connecting to account {cloud_email}")
        except asyncio.exceptions.CancelledError:
            return True
    except ConnectionError:
        await hass.async_add_executor_job(cloud.disconnect)
        raise ConfigEntryNotReady(
            f"Connection error connecting to account {cloud_email}"
        )
    except requests.exceptions.ConnectionError:
        LOGGER.log(
            LoggerType.API,
            "Name resolution error connecting to cloud API endpoint - retrying later",
            log_level=LogLevel.ERROR,
        )
        await hass.async_add_executor_job(cloud.disconnect)
        raise ConfigEntryNotReady(
            f"Connection error connecting to cloud API endpoint"
        )

    hass.data[DOMAIN][entry.entry_id] = {
        ATTR_CLOUD: cloud,
        ATTR_DEVICES: {},
        ATTR_DEVICEIDS: {},
        ATTR_FEATUREBITS: {},
        CONF_EMAIL: cloud_email,
        CONF_PASSWORD: cloud_password,
        CONF_TYPE: cloud_type,
    }

    for name, device in cloud.devices.items():
        await async_init_device(hass, entry, name, device)

    return True


async def async_init_device(hass, entry, name, device) -> None:
    """Initialize a device."""
    LOGGER.log(
        LoggerType.SETUP,
        "Setting up device '%s' on account '%s'",
        name,
        hass.data[DOMAIN][entry.entry_id][CONF_EMAIL],
    )
    api = LandroidAPI(hass, name, entry)
    hass.data[DOMAIN][entry.entry_id][ATTR_DEVICEIDS].update({name: None})
    hass.data[DOMAIN][entry.entry_id][ATTR_DEVICES].update(
        {name: {ATTR_API: api, ATTR_DEVICE: device}}
    )


async def check_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check if a device unique ID is set."""
    if not isinstance(entry.unique_id, type(None)):
        return

    new_unique_id = f"{entry.data.get(CONF_EMAIL)}_{entry.data.get(CONF_TYPE)}"

    data = {
        CONF_EMAIL: entry.data[CONF_EMAIL],
        CONF_PASSWORD: entry.data[CONF_PASSWORD],
        CONF_TYPE: entry.data[CONF_TYPE],
    }

    hass.config_entries.async_update_entry(entry, data=data, unique_id=new_unique_id)
