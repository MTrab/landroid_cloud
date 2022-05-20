"""Support for Landroid Cloud compatible sensor."""
from __future__ import annotations

import logging
import voluptuous as vol

from functools import partial
from typing import Any
from homeassistant.components import sensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level

from .const import (
    ATTR_ZONE,
    DOMAIN,
    SERVICE_SETZONE,
    SERVICE_START,
    SERVICE_HOME,
    STATE_INITIALIZING,
    STATE_OFFLINE,
    UPDATE_SIGNAL,
)
from .sensor_definition import API_WORX_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_devices):
    """Setup sensor platform from a config entry."""
    config = config_entry

    entities = []

    for sensor_type in API_WORX_SENSORS:
        api = hass.data[DOMAIN][config.entry_id]["api"]
        _LOGGER.debug("Init Landroid %s sensor for %s", sensor_type, api.friendly_name)
        entity = LandroidSensor(api, hass, sensor_type)
        entities.append(entity)

    async_add_devices(entities, True)

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_START,
        {},
        "async_start",
    )

    platform.async_register_entity_service(
        SERVICE_HOME,
        {},
        "async_home",
    )

    platform.async_register_entity_service(
        SERVICE_SETZONE,
        {vol.Required(ATTR_ZONE): vol.All(vol.Coerce(int), vol.Range(0, 3))},
        "async_setzone",
    )

    return True


class LandroidSensor(Entity):
    """Class to create and populate a Landroid Sensor."""

    def __init__(self, api, hass, sensor_type):
        """Init new sensor."""

        self.api = api
        self.hass = hass
        self._attributes = {}
        self._available = False
        self._name = f"{api.friendly_name} {sensor_type}"
        if sensor_type == "status":
            self._name = api.friendly_name

        self._state = STATE_INITIALIZING
        self._sensor_type = sensor_type
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{api.name}_{sensor_type}")
        self._unique_id = f"{api.device.serial_number}_{sensor_type}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.api.entry_id, self.api.friendly_name)},
            "name": self.name,
            "model": f"Firmware: {self.api.device.firmware_version}",
            "manufacturer": self.api.data.get(CONF_TYPE),
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return sensor attributes."""
        return self._attributes

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return API_WORX_SENSORS[self._sensor_type]["unit"]

    @property
    def icon(self):
        """Icon to use in the frontend."""
        if self._sensor_type == "battery" and isinstance(self.state, int):
            charging = self._attributes["charging"]
            return icon_for_battery_level(battery_level=self.state, charging=charging)

        return API_WORX_SENSORS[self._sensor_type]["icon"]

    @property
    def should_poll(self):
        """Return False as entity is updated from the component."""
        return False

    @property
    def state(self):
        """Return sensor state."""
        return self._state

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        await super().async_added_to_hass()
        _LOGGER.debug("Added sensor %s", self.entity_id)
        await self.api.async_refresh()
        async_dispatcher_connect(
            self.hass, f"{UPDATE_SIGNAL}_{self.api.index}", self.update_callback
        )

    def _get_data(self):
        """Return new data from the api cache."""
        data = self.api.get_data(self._sensor_type)
        self._available = True
        return data

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update the sensor."""
        _LOGGER.debug("Updating %s", self.entity_id)
        data = self._get_data()
        if "state" in data:
            _LOGGER.debug(data)
            state = data.pop("state")
            self._attributes.update(data)

            # Set state to offline if mower is not online
            if self._sensor_type == "status":
                _LOGGER.debug(
                    "Mower %s online: %s", self._name, self._attributes["online"]
                )
                if not self._attributes["online"]:
                    state = STATE_OFFLINE

            _LOGGER.debug("Mower %s State %s", self._name, state)
            self._state = state
            if "latitude" in self._attributes:
                if self._attributes["latitude"] is None:
                    del self._attributes["latitude"]
                    del self._attributes["longitude"]
        else:
            _LOGGER.debug("No data received for %s", self.entity_id)
            reachable = self.api.device.online
            if not reachable:
                if "_battery" in self.entity_id:
                    self._state = STATE_UNKNOWN
                else:
                    self._state = STATE_OFFLINE

    async def async_start(self, **kwargs: Any) -> None:
        """Start grass cutting routine."""
        if self._sensor_type == "status":
            _LOGGER.debug("Starting %s", self._name)
            await self.hass.async_add_executor_job(
                partial(self.api.device.start, **kwargs)
            )

    async def async_home(self, **kwargs: Any) -> None:
        """Stop and return to base."""
        if self._sensor_type == "status":
            _LOGGER.debug("Stopping %s", self._name)
            await self.hass.async_add_executor_job(
                partial(self.api.device.stop, **kwargs)
            )

    async def async_setzone(self, zone: int) -> None:
        """Set next zone to cut."""
        if self._sensor_type == "status":
            _LOGGER.debug("Setting zone for %s to %s", self._name, zone)
            await self.hass.async_add_executor_job(
                partial(self.api.device.setzone, zone)
            )
