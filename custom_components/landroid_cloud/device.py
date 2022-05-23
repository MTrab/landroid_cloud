"""Define device classes."""
from __future__ import annotations

import logging

from homeassistant.components.vacuum import ENTITY_ID_FORMAT, VacuumEntityFeature
from homeassistant.const import CONF_TYPE
from homeassistant.core import callback
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.entity import Entity

from .attribute_map import ATTR_MAP

from .const import (
    DOMAIN,
    STATE_INITIALIZING,
    STATE_OFFLINE,
)

from .pyworxcloud import WorxCloud

# Commonly supported features
SUPPORT_LANDROID = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.STOP
)

_LOGGER = logging.getLogger(__name__)


class LandroidCloudBase(Entity):
    """Define a base class."""

    def __init__(self, hass, api):
        """Init new base device."""

        self.api = api
        self.hass = hass

        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name}")

        self._attributes = {}
        self._available = False
        self._battery_level = None
        self._name = f"{api.friendly_name}"
        self._unique_id = f"{api.device.serial_number}_{api.name}"
        self._state = STATE_INITIALIZING
        self._serialnumber = None
        self._mac = None
        self._connections = {}
        self._icon = None

    @property
    def extra_state_attributes(self):
        """Return sensor attributes."""
        return self._attributes

    @property
    def device_info(self):
        return {
            "connections": self._connections,
            "identifiers": {(DOMAIN, self.api.entry_id, self.api.friendly_name)},
            "name": str(self.name),
            "sw_version": self.api.device.firmware_version,
            "manufacturer": self.api.data.get(CONF_TYPE),
            "model": None,
        }

    @property
    def robot_unique_id(self):
        """Return the unique id."""
        return f"landroid_{self._serialnumber}"

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self._battery_level

    @property
    def _robot_state(self):
        """Return the state of the deevice."""
        # try:
        #     state = STATE_MAP[phase]
        # except KeyError:
        #     return STATE_ERROR
        # if cycle != "none" and state in (STATE_IDLE, STATE_DOCKED):
        #     state = STATE_PAUSED
        # return state
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def state(self):
        """Return sensor state."""
        return self._state

    # def _get_data(self):
    #     """Return new data from the api cache."""
    #     data = self.api.get_data()
    #     self._available = True
    #     return data

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update the sensor."""
        _LOGGER.debug("Updating %s", self.entity_id)
        master: WorxCloud = self.api.device

        methods = ATTR_MAP["default"]
        data = {}
        self._icon = methods["icon"]
        for prop, attr in methods["state"].items():
            if hasattr(master, prop):
                prop_data = getattr(master, prop)
                data[attr] = prop_data
        _LOGGER.debug(data)

        # if "state" in data:
        state = master.status_description
        self._attributes.update(data)

        # Set state to offline if mower is not online
        _LOGGER.debug("Mower %s online: %s", self._name, master.online)
        if not master.online:
            state = STATE_OFFLINE

        _LOGGER.debug("Mower %s State %s", self._name, state)
        self._state = state
        if "latitude" in self._attributes:
            if self._attributes["latitude"] is None:
                del self._attributes["latitude"]
                del self._attributes["longitude"]

        self._mac = master.mac
        self._serialnumber = master.serial
        self._connections = {(dr.CONNECTION_NETWORK_MAC, self._mac)}
        # else:
        #     _LOGGER.debug("No data received for %s", self.entity_id)
        #     reachable = self.api.device.online
        #     if not reachable:
        #         if "_battery" in self.entity_id:
        #             self._state = STATE_UNKNOWN
        #         else:
        #             self._state = STATE_OFFLINE


class WorxDevice(LandroidCloudBase):
    """Definition of Worx Landroid device."""

    # def __init__(self, hass, api):
    #     """Init new base device."""
    #     super().__init__(hass, api)

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORT_LANDROID


class KressDevice(LandroidCloudBase):
    """Definition of Kress device."""


class LandxcapeDevice(LandroidCloudBase):
    """Definition of Landxcape device."""
