"""Define device classes."""
from __future__ import annotations
from functools import partial

import logging

from homeassistant.components.vacuum import (
    ENTITY_ID_FORMAT,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.const import CONF_TYPE
from homeassistant.core import callback, ServiceCall
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.entity import Entity

from pyworxcloud import WorxCloud
from pyworxcloud.states import STATE_TO_DESCRIPTION, ERROR_TO_DESCRIPTION

from .attribute_map import ATTR_MAP

from .const import (
    DOMAIN,
    STATE_INITIALIZING,
    STATE_MAP,
    STATE_MOWING,
    STATE_OFFLINE,
    STATE_RAINDELAY,
    UPDATE_SIGNAL,
)

# Commonly supported features
SUPPORT_LANDROID_BASE = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
)

_LOGGER = logging.getLogger(__name__)


class LandroidCloudBase(StateVacuumEntity, Entity):
    """Define a base class."""

    _battery_level: int | None = None
    _attr_state = STATE_INITIALIZING

    def __init__(self, hass, api):
        """Init new base device."""

        self.api = api
        self.hass = hass

        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name}")

        self._attributes = {}
        self._available = False
        self._name = f"{api.friendly_name}"
        self._unique_id = f"{api.device.serial_number}_{api.name}"
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
            "model": self.api.device.board,
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

    # @property
    # def _robot_state(self):
    #     """Return the state of the device."""
    #     return self._attr_state

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
        return self._attr_state

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        await super().async_added_to_hass()
        _LOGGER.debug("Added sensor %s", self.entity_id)
        await self.api.async_refresh()
        async_dispatcher_connect(
            self.hass,
            f"{UPDATE_SIGNAL}_{self.api.device.name}",
            self.update_callback,
        )

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
                if not isinstance(prop_data, type(None)):
                    data[attr] = prop_data
        data["error"] = ERROR_TO_DESCRIPTION[master.error or 0]
        _LOGGER.debug(data)

        try:
            state = STATE_MAP[master.status]
        except KeyError:
            state = STATE_INITIALIZING

        self._attributes.update(data)

        _LOGGER.debug("Mower %s online: %s", self._name, master.online)
        self._available = master.online
        if not master.online:
            state = STATE_OFFLINE

        if master.error is not None:
            if master.error > 0 and master.error != 5:
                state = STATE_ERROR
            elif master.error == 5:
                state = STATE_RAINDELAY

        _LOGGER.debug("Mower %s state '%s'", self._name, state)
        # self._state = state
        self._attr_state = state

        self._mac = master.mac
        self._serialnumber = master.serial
        self._connections = {(dr.CONNECTION_NETWORK_MAC, self._mac)}
        self._battery_level = master.battery_percent

    async def async_start(self):
        """Start or resume the task."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Starting %s", self._name)
        await self.hass.async_add_executor_job(device.start)

    async def async_pause(self):
        """Pause the cleaning cycle."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Pausing %s", self._name)
        await self.hass.async_add_executor_job(device.pause)

    async def async_return_to_base(self):
        """Set the vacuum cleaner to return to the dock."""
        if self.state != STATE_DOCKED and self.state != STATE_RETURNING:
            device: WorxCloud = self.api.device
            _LOGGER.debug("Sending %s back to dock", self._name)
            await self.hass.async_add_executor_job(device.home)

    async def async_setzone(self, service_call: ServiceCall):
        """Set next zone to cut."""
        device: WorxCloud = self.api.device
        zone = service_call.data["zone"]
        _LOGGER.debug("Setting zone for %s to %s", self._name, zone)
        await self.hass.async_add_executor_job(partial(device.setzone, str(zone)))
