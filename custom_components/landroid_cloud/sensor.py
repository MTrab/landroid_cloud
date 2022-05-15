"""Support for monitoring Worx Landroid Sensors."""
import logging

from homeassistant.components import sensor
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level

from . import API_WORX_SENSORS, LANDROID_API, UPDATE_SIGNAL
from .const import STATE_INITIALIZING, STATE_OFFLINE

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None): # pylint: disable=unused-argument
    """Set up the available sensors for Worx Landroid."""
    if discovery_info is None:
        return

    entities = []

    info = discovery_info[0]
    for tsensor in API_WORX_SENSORS:
        name = f"{info['name'].lower()}_{tsensor.lower()}"
        friendly_name = f"{info['friendly']} {tsensor}"
        dev_id = info["id"]
        api = hass.data[LANDROID_API][dev_id]
        sensor_type = tsensor
        _LOGGER.debug("Init Landroid %s sensor for %s", sensor_type, info["friendly"])
        entity = LandroidSensor(api, name, sensor_type, friendly_name, dev_id)
        entities.append(entity)

    async_add_entities(entities, True)


class LandroidSensor(Entity):
    """Class to create and populate a Landroid Sensor."""

    def __init__(self, api, name, sensor_type, friendly_name, dev_id):
        """Init new sensor."""

        self._api = api
        self._attributes = {}
        self._available = False
        self._name = friendly_name
        self._state = STATE_INITIALIZING
        self._sensor_type = sensor_type
        self._dev_id = dev_id
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(name)

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

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        async_dispatcher_connect(self.hass, UPDATE_SIGNAL, self.update_callback)

    def _get_data(self):
        """Return new data from the api cache."""
        data = self._api.get_data(self._sensor_type)
        self._available = True
        return data

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
                if not self._api.client.online:
                    state = STATE_OFFLINE

            _LOGGER.debug("Mower %s State %s", self._name, state)
            self._state = state
            if "latitude" in self._attributes:
                if self._attributes["latitude"] is None:
                    del self._attributes["latitude"]
                    del self._attributes["longitude"]
        else:
            _LOGGER.debug("No data received for %s", self.entity_id)
            reachable = self._api.client.online
            if not reachable:
                if "_battery" in self.entity_id:
                    self._state = STATE_UNKNOWN
                else:
                    self._state = STATE_OFFLINE
