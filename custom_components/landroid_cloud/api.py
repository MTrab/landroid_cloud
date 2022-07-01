"""Representing the Landroid Cloud API interface."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util import slugify as util_slugify
from pyworxcloud import WorxCloud
from pyworxcloud.events import LandroidEvent
from pyworxcloud.utils import Capability, DeviceCapability, DeviceHandler

from .const import ATTR_CLOUD, DOMAIN, UPDATE_SIGNAL, LandroidFeatureSupport
from .utils.logger import LandroidLogger, LoggerType


class LandroidAPI:
    """Handle the API calls."""

    def __init__(self, hass: HomeAssistant, device_name: str, entry: ConfigEntry):
        """Initialize API connection for a device.

        Args:
            hass (HomeAssistant): Home Assistant object
            index (int): Device number to connect to. 0 is the first device associated.
            device (WorxCloud): pyWorxlandroid object for the connection.
            entry (ConfigEntry): Home Assistant configuration entry for the cloud account.
        """
        self.hass = hass
        self.entry_id = entry.entry_id
        self.data = entry.data
        self.options = entry.options
        self.cloud: WorxCloud = hass.data[DOMAIN][entry.entry_id][ATTR_CLOUD]
        self.device: DeviceHandler = self.cloud.devices[device_name]
        self.unique_id = entry.unique_id
        self.services = {}
        self.shared_options = {}
        self.device_id = None
        self.features = 0
        self.features_loaded = False

        self._last_state = self.device.online

        self.name = util_slugify(f"{device_name}")
        self.friendly_name = device_name

        self.config = {
            "email": hass.data[DOMAIN][entry.entry_id][CONF_EMAIL].lower(),
            "password": hass.data[DOMAIN][entry.entry_id][CONF_PASSWORD],
            "type": hass.data[DOMAIN][entry.entry_id][CONF_TYPE].lower(),
        }

        self.logger = LandroidLogger(name=__name__, api=self)
        self.cloud.set_callback(LandroidEvent.DATA_RECEIVED, self.receive_data)
        self.device.mqtt.set_eventloop(self.hass.loop)

    def check_features(self, features: int, callback_func: Any = None) -> None:
        """Check which features the device supports.

        Args:
            features (int): Current feature set.
            callback_func (_type_, optional):
                Function to be called when the features
                have been assessed. Defaults to None.
        """

        capabilities: Capability = self.device.capabilities
        if capabilities.check(DeviceCapability.PARTY_MODE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Party mode capable")
            features = features | LandroidFeatureSupport.PARTYMODE

        if capabilities.check(DeviceCapability.ONE_TIME_SCHEDULE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "OTS capable")
            features = (
                features | LandroidFeatureSupport.EDGECUT | LandroidFeatureSupport.OTS
            )

        if capabilities.check(DeviceCapability.TORQUE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Torque capable")
            features = features | LandroidFeatureSupport.TORQUE

        self.features = features
        self.features_loaded = True

        if callback_func:
            callback_func()

    @callback
    def receive_data(
        self, name: str, device: DeviceHandler  # pylint: disable=unused-argument
    ) -> None:
        """Callback function when the API sends new data."""
        self.logger.log(
            LoggerType.DATA_UPDATE,
            "Received new data from API to %s, dispatching %s",
            name,
            util_slugify(f"{UPDATE_SIGNAL}_{name}"),
            device=name,
        )
        dispatcher_send(self.hass, util_slugify(f"{UPDATE_SIGNAL}_{name}"))
