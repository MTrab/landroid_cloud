"""Adds support for Landroid Cloud compatible devices."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform, CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.loader import async_get_integration
from homeassistant.util import slugify as util_slugify
from pyworxcloud import WorxCloud

from .const import DOMAIN, LANDROID_API, STARTUP, UPDATE_SIGNAL
from .sensor_definition import API_WORX_SENSORS

_LOGGER = logging.getLogger(__name__)
_PLATFORMS = [Platform.SENSOR]

CLIENTS = []


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""

    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for conf in config[DOMAIN]:
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
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)
    result = await _setup(hass, entry)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        for unsub in hass.data[DOMAIN][entry.entry_id].listeners:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id)

        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup the integration using a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    cloud_email = entry.data.get(CONF_EMAIL)
    cloud_password = entry.data.get(CONF_PASSWORD)
    cloud_type = entry.data.get(CONF_TYPE)

    dev = 0

    master = WorxCloud()
    auth = await hass.async_add_executor_job(
        master.initialize,
        cloud_email,
        cloud_password,
        cloud_type.lower(),
    )

    if not auth:
        _LOGGER.warning("Error in authentication!")
        return False

    try:
        num_dev = await hass.async_add_executor_job(master.enumerate)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.warning(err)
        return False

    for device in range(num_dev):
        CLIENTS.append(dev)
        _LOGGER.debug("Setting up device %s (%s)", device, cloud_email)
        CLIENTS[dev] = WorxCloud()
        await hass.async_add_executor_job(
            CLIENTS[dev].initialize, cloud_email, cloud_password, cloud_type.lower()
        )
        await hass.async_add_executor_job(CLIENTS[dev].connect, device, False)

        api = WorxLandroidAPI(hass, dev, CLIENTS[dev], entry)
        hass.data[DOMAIN][entry.entry_id] = api
        dev += 1

    return True


class WorxLandroidAPI:
    """Handle the API calls."""

    def __init__(self, hass: HomeAssistant, index: int, device, entry: ConfigEntry):
        """Set up device."""
        self._hass = hass
        self.entry_id = entry.entry_id
        self.data = entry.data
        self.options = entry.options
        self.device = device
        self.index = index
        self.listeners = []

        _LOGGER.debug(self.device.name)
        self.name = util_slugify(f"{self.device.name}")
        self.friendly_name = self.device.name

    def get_data(self, sensor_type):
        """Get data from state cache."""
        methods = API_WORX_SENSORS[sensor_type]
        data = {}

        for prop, attr in methods["state"].items():
            if hasattr(self.device, prop):
                prop_data = getattr(self.device, prop)
                data[attr] = prop_data
        return data

    async def async_refresh(self):
        """Try fetching data from cloud."""
        await self._hass.async_add_executor_job(self.device.getStatus)
        dispatcher_send(self._hass, f"{UPDATE_SIGNAL}_{self.index}")

    async def async_update(self):
        """Update the state cache from cloud API."""
        dispatcher_send(self._hass, f"{UPDATE_SIGNAL}_{self.index}")
