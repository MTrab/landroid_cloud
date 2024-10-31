"""Representing the Landroid Cloud API interface."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util import slugify as util_slugify
from pyworxcloud import WorxCloud
from pyworxcloud.events import LandroidEvent
from pyworxcloud.utils import DeviceCapability, DeviceHandler

from .const import (
    API_TO_INTEGRATION_FEATURE_MAP,
    ATTR_CLOUD,
    DOMAIN,
    UPDATE_SIGNAL,
    LandroidFeatureSupport,
)
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
        self.entry = entry
        self.cloud: WorxCloud = hass.data[DOMAIN][entry.entry_id][ATTR_CLOUD]
        self.device: DeviceHandler = self.cloud.devices[device_name]
        self.unique_id = entry.unique_id
        self.services = {}
        self.shared_options = {}
        self.device_id = None
        self.features = 0
        self.features_loaded = False

        self.device_name = device_name

        self.cloud.update(self.device.serial_number)
        self.cloud._decode_data(self.device)

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

        self.logger.log(LoggerType.API, "Device: %s", self.cloud.devices[device_name])

    def mqtt_conn_check(self, state: bool) -> None:
        """Check connection state."""
        if state is False:
            asyncio.run_coroutine_threadsafe(
                self.cloud.connect(), self.hass.loop
            ).result()

    async def async_await_features(self, timeout: int = 10) -> None:
        """Used to await feature checks."""
        timeout_at = datetime.now() + timedelta(seconds=timeout)

        while not self.features_loaded:
            if datetime.now() > timeout_at:
                break

        if (
            not self.device.capabilities.ready
            or not self.features_loaded
            or self.features == 0
        ):
            raise ValueError(
                f"Capabilities ready: {self.device.capabilities.ready} -- Features loaded: {self.features_loaded} -- Feature bits: {self.features}"
            )

        self.device.mqtt.set_eventloop(self.hass.loop)

    def check_features(
        self, features: int | None = None, callback_func: Any = None
    ) -> None:
        """Check which features the device supports.

        Args:
            features (int): Current feature set.
            callback_func (_type_, optional):
                Function to be called when the features
                have been assessed. Defaults to None.
        """
        self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Assessing available features")
        if isinstance(features, type(None)):
            features = self.features

        # capabilities: Capability = self.device.capabilities

        if self.has_feature(DeviceCapability.PARTY_MODE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Party mode capable")
            features = features | LandroidFeatureSupport.PARTYMODE

        if self.has_feature(DeviceCapability.ONE_TIME_SCHEDULE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "OTS capable")
            features = features | LandroidFeatureSupport.OTS

        # if self.has_feature(DeviceCapability.EDGE_CUT):
        #     self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Edge Cut capable")
        features = features | LandroidFeatureSupport.EDGECUT

        if self.has_feature(DeviceCapability.TORQUE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Torque capable")
            features = features | LandroidFeatureSupport.TORQUE

        old_feature = self.features
        self.features = features

        if callback_func:
            callback_func(old_feature)

    def has_feature(self, api_feature: DeviceCapability) -> bool:
        """Check if the feature is already known.

        Return True if feature is supported and not known to us.
        Returns False if not supported or already known.
        """

        if API_TO_INTEGRATION_FEATURE_MAP[api_feature] & self.features != 0:
            return False
        else:
            return self.device.capabilities.check(api_feature)

    @callback
    def receive_data(
        self, name: str, device: DeviceHandler  # pylint: disable=unused-argument
    ) -> None:
        """Callback function when the MQTT broker sends new data."""
        self.logger.log(
            LoggerType.DATA_UPDATE,
            "Received new data from MQTT to %s, dispatching %s",
            name,
            util_slugify(f"{UPDATE_SIGNAL}_{name}"),
            device=name,
        )
        dispatcher_send(self.hass, util_slugify(f"{UPDATE_SIGNAL}_{name}"))
