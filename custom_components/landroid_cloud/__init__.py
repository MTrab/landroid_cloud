"""Adds support for Landroid Cloud compatible devices."""
from __future__ import annotations
import asyncio

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from pyworxcloud import WorxCloud, exceptions

from .api import LandroidAPI
from .const import (
    DOMAIN,
    LOGLEVEL,
    PLATFORMS,
    STARTUP,
)
from .scheme import CONFIG_SCHEMA  # Used for validating YAML config - DO NOT DELETE!
from .services import async_setup_services
from .utils.logger import LandroidLogger, LogLevel, LoggerType

LOGGER = LandroidLogger(name=__name__, log_level=LOGLEVEL)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""

    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for conf in config[DOMAIN]:
        LOGGER.log(
            LoggerType.SETUP_IMPORT,
            "Importing configuration for %s from configuration.yaml",
            conf["email"],
        )
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up cloud API connector from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await check_unique_id(hass, entry)
    result = await _setup(hass, entry)

    if result:
        hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async_setup_services(hass)

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    services = []
    if unload_ok:
        for device in range(hass.data[DOMAIN][entry.entry_id]["count"]):
            await hass.async_add_executor_job(
                hass.data[DOMAIN][entry.entry_id][device]["device"].disconnect
            )
            services.extend(hass.data[DOMAIN][entry.entry_id][device]["api"].services)

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


async def _setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup the integration using a config entry."""
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
    master = WorxCloud(cloud_email, cloud_password, cloud_type.lower())
    auth = False
    try:
        auth = await hass.async_add_executor_job(master.authenticate)
    except exceptions.RequestError:
        LOGGER.log(
            LoggerType.API,
            "Request for %s was malformed.",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.AuthorizationError:
        LOGGER.log(
            LoggerType.API,
            "Unauthorized - please check your credentials for %s at Landroid Cloud",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.ForbiddenError:
        LOGGER.log(
            LoggerType.API,
            "Server rejected access for %s at Landroid Cloud - this might be "
            "temporary due to high numbers of API requests from this IP address.",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.NotFoundError:
        LOGGER.log(
            LoggerType.API,
            "Endpoint for %s was not found.",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.TooManyRequestsError:
        LOGGER.log(
            LoggerType.API,
            "Too many requests for %s at Landroid Cloud. IP address temporary banned.",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.InternalServerError:
        LOGGER.log(
            LoggerType.API,
            "Internal server error happend for the request to %s at Landroid Cloud.",
            cloud_email,
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.ServiceUnavailableError:
        LOGGER.log(
            LoggerType.API,
            "Service at Landroid Cloud was unavailable.",
            log_level=LogLevel.ERROR,
        )
        return False
    except exceptions.APIException as ex:
        LOGGER.log(
            LoggerType.API,
            "%s",
            ex,
            log_level=LogLevel.ERROR,
        )
        return False

    if not auth:
        LOGGER.log(
            LoggerType.AUTHENTICATION,
            "Error in authentication for %s",
            cloud_email,
            log_level=LogLevel.WARNING,
        )
        return False

    try:
        num_dev = await hass.async_add_executor_job(master.enumerate)
    except Exception as err:  # pylint: disable=broad-except
        LOGGER.log(LoggerType.AUTHENTICATION, "%s", err, log_level=LogLevel.WARNING)
        return False

    hass.data[DOMAIN][entry.entry_id] = {
        "count": num_dev,
        CONF_EMAIL: cloud_email,
        CONF_PASSWORD: cloud_password,
        CONF_TYPE: cloud_type,
    }

    hass.data[DOMAIN][entry.entry_id]["device_ids"] = []

    await asyncio.gather(
        *[
            async_init_device(
                hass, entry, device, cloud_email, cloud_password, cloud_type
            )
            for device in range(num_dev)
        ]
    )

    return True


async def async_init_device(
    hass, entry, device, cloud_email, cloud_password, cloud_type
) -> None:
    """Initialize the device."""
    hass.data[DOMAIN][entry.entry_id][device] = {}

    LOGGER.log(LoggerType.SETUP, "Setting up device no. %s on %s", device, cloud_email)
    # Init the object
    hass.data[DOMAIN][entry.entry_id][device]["device"] = WorxCloud(
        cloud_email, cloud_password, cloud_type.lower()
    )
    # Authenticate
    await hass.async_add_executor_job(
        hass.data[DOMAIN][entry.entry_id][device]["device"].authenticate
    )
    # Connect
    await hass.async_add_executor_job(
        hass.data[DOMAIN][entry.entry_id][device]["device"].connect, device, False
    )
    # Get initial data
    await hass.async_add_executor_job(
        hass.data[DOMAIN][entry.entry_id][device]["device"].update
    )
    api = LandroidAPI(hass, device, hass.data[DOMAIN][entry.entry_id][device], entry)
    hass.data[DOMAIN][entry.entry_id][device]["api"] = api


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
