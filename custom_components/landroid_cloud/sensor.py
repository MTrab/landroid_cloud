"""Sensors for landroid_cloud."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.util import slugify as util_slugify

from .device_base import LandroidSensorEntityDescription

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN, UPDATE_SIGNAL
from .utils.entity_setup import vendor_to_device

LOGGER = logging.getLogger(__name__)

SENSORS = [
    LandroidSensorEntityDescription(
        key="battery_state",
        name="Battery",
        entity_category=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        value_fn=lambda landroid: landroid.battery["percent"] if "percent" in landroid.battery else None,
        attributes=["cycles","temperature","voltage","charging"]
    )
]

async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the mower device."""
    sensors = []
    for name, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        device = vendor_to_device(api.config["type"])
        # constructor = device.MowerDevice(hass, api)
        for sens in SENSORS:
            entity = LandroidSensor(hass, sens, api, config)

            sensors.append(entity)

    async_add_devices(sensors)


class LandroidSensor(SensorEntity):
    """Representation of a Landroid sensor."""

    def __init__(self,hass:HomeAssistant, description:LandroidSensorEntityDescription, api:LandroidAPI, config:ConfigEntry)->None:
        """Initialize a Landroid sensor."""
        super().__init__()

        self.entity_description = description
        self.hass = hass
        self.device = api.device

        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name
        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}"
        )
        self._attr_should_poll = False

        self._attr_native_value = self.entity_description.value_fn(
            self.device
        )

        LOGGER.info("Added sensor '%s' with value '%s'", self._attr_name,self._attr_native_value)

        _connections = {(dr.CONNECTION_NETWORK_MAC, self.device.mac_address)}

        self._attr_device_info = {
            "connections": _connections,
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._api.device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._api.device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._api.device.model,
        }

        self._attr_extra_state_attributes = {}

        if not isinstance(self.entity_description.attributes, type(None)):
            if self.entity_description.key == "battery_state":
                for key in self.entity_description.attributes:
                    self._attr_extra_state_attributes.update({key: self.device.battery[key]})

        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._api.device.name}"),
            self.async_write_ha_state,
        )