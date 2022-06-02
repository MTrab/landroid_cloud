"""Adds support for Landroid Cloud compatible devices."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.loader import async_get_integration
from homeassistant.util import slugify as util_slugify

from pyworxcloud import WorxCloud

from .const import DOMAIN, PLATFORMS, STARTUP, UPDATE_SIGNAL
from .scheme import CONFIG_SCHEMA

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""

    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for conf in config[DOMAIN]:
        _LOGGER.debug("Importing %s from configuration.yaml", conf["email"])
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
    _LOGGER.debug("Entry unique ID: %s", entry.unique_id)
    hass.data.setdefault(DOMAIN, {})

    await check_unique_id(hass, entry)
    result = await _setup(hass, entry)

    # for platform in PLATFORMS:
    #     hass.async_create_task(
    #         hass.config_entries.async_forward_entry_setup(entry, platform)
    #     )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # unload_ok = await hass.config_entries.async_forward_entry_unload(entry, platform)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        for unsub in hass.data[DOMAIN][entry.entry_id]["api"].listeners:
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

    if cloud_type is None:
        cloud_type = "worx"

    _LOGGER.debug("Opening connection to account for %s as %s", cloud_email, cloud_type)
    master = WorxCloud(cloud_email, cloud_password, cloud_type.lower())
    auth = await hass.async_add_executor_job(master.initialize)

    if not auth:
        _LOGGER.warning("Error in authentication! (%s)", cloud_email)
        return False

    try:
        num_dev = await hass.async_add_executor_job(master.enumerate)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.warning(err)
        return False

    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id]["clients"] = []

    for device in range(num_dev):
        hass.data[DOMAIN][entry.entry_id]["clients"].append(device)
        _LOGGER.debug("Setting up device %s (%s)", device, cloud_email)
        hass.data[DOMAIN][entry.entry_id]["clients"][device] = WorxCloud(
            cloud_email, cloud_password, cloud_type.lower()
        )
        await hass.async_add_executor_job(
            hass.data[DOMAIN][entry.entry_id]["clients"][device].initialize
        )
        await hass.async_add_executor_job(
            hass.data[DOMAIN][entry.entry_id]["clients"][device].connect, device, False
        )
        api = LandroidAPI(
            hass, device, hass.data[DOMAIN][entry.entry_id]["clients"][device], entry
        )
        hass.data[DOMAIN][entry.entry_id]["api"] = api

    return True


async def check_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check if a device unique ID is set."""
    if not isinstance(entry.unique_id, type(None)):
        return

    new_unique_id = f"{entry.data.get(CONF_EMAIL)}_{entry.data.get(CONF_TYPE)}"

    _LOGGER.debug("New unique id: %s", new_unique_id)

    data = {
        CONF_EMAIL: entry.data[CONF_EMAIL],
        CONF_PASSWORD: entry.data[CONF_PASSWORD],
        CONF_TYPE: entry.data[CONF_TYPE],
    }
    result = hass.config_entries.async_update_entry(
        entry, data=data, unique_id=new_unique_id
    )
    _LOGGER.debug("Update successful? %s", result)


class LandroidAPI:
    """Handle the API calls."""

    def __init__(
        self, hass: HomeAssistant, index: int, device: WorxCloud, entry: ConfigEntry
    ):
        """Set up device."""
        self._hass = hass
        self.entry_id = entry.entry_id
        self.data = entry.data
        self.options = entry.options
        self.device = device
        self.index = index
        self.listeners = []
        self.services = []
        self.unique_id = entry.unique_id

        self.name = util_slugify(f"{self.device.name}")
        self.friendly_name = self.device.name

        self.device.set_callback(self.receive_data)

    def receive_data(self):
        """Used as callback from API when data is received."""
        _LOGGER.debug(
            "Update signal received from API on %s for device %s",
            self.data.get(CONF_EMAIL),
            self.device.name,
        )
        dispatcher_send(self._hass, f"{UPDATE_SIGNAL}_{self.device.name}")

    async def async_refresh(self):
        """Try fetching data from cloud."""
        await self._hass.async_add_executor_job(self.device.update)
        dispatcher_send(self._hass, f"{UPDATE_SIGNAL}_{self.device.name}")

    async def async_update(self):
        """Update the state cache from cloud API."""
        dispatcher_send(self._hass, f"{UPDATE_SIGNAL}_{self.device.name}")
