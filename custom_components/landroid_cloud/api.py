"""Representing the Landroid Cloud API interface."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util import slugify as util_slugify

from pyworxcloud import WorxCloud, exceptions

from .const import (
    DOMAIN,
    UPDATE_SIGNAL,
    LandroidFeatureSupport,
)

from .utils.logger import LandroidLogger, LoggerType, LogLevel


class LandroidAPI:
    """Handle the API calls."""

    def __init__(
        self, hass: HomeAssistant, index: int, device: WorxCloud, entry: ConfigEntry
    ):
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
        self.device: WorxCloud = device["device"]
        self.index = index
        self.unique_id = entry.unique_id
        self.services = {}
        self.shared_options = {}
        self.device_id = None
        self.features = 0
        self.features_loaded = False

        self._last_state = self.device.online

        self.name = util_slugify(f"{self.device.name}")
        self.friendly_name = self.device.name

        self.config = {
            "email": hass.data[DOMAIN][entry.entry_id][CONF_EMAIL].lower(),
            "password": hass.data[DOMAIN][entry.entry_id][CONF_PASSWORD],
            "type": hass.data[DOMAIN][entry.entry_id][CONF_TYPE].lower(),
        }

        self.logger = LandroidLogger(name=__name__, api=self)
        self.device.set_callback(self.receive_data)

    def check_features(self, features: int, callback=None) -> None:
        """Check which features the device supports.

        Args:
            features (int): Current feature set.
            callback (_type_, optional):
                Function to be called when the features
                have been assessed. Defaults to None.
        """

        if self.device.partymode_capable:
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Party mode capable")
            features = features | LandroidFeatureSupport.PARTYMODE

        if self.device.ots_capable:
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "OTS capable")
            features = (
                features | LandroidFeatureSupport.EDGECUT | LandroidFeatureSupport.OTS
            )

        if self.device.torque_capable:
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Torque capable")
            features = features | LandroidFeatureSupport.TORQUE

        self.features = features
        self.features_loaded = True

        if callback:
            callback()

    def receive_data(self) -> None:
        """Callback function when the API sends new data."""
        if not self._last_state and self.device.online:
            self._last_state = True
            self.hass.config_entries.async_reload(self.entry_id)

        self.logger.log(
            LoggerType.DATA_UPDATE,
            "Received new data from API, dispatching %s",
            f"{UPDATE_SIGNAL}_{self.device.name}",
        )
        dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.device.name}")

    async def async_refresh(self):
        """Try fetching data from cloud."""
        try:
            await self.hass.async_add_executor_job(self.device.update)
        except exceptions.RequestError:
            self.logger.log(
                LoggerType.API,
                "Request for %s was malformed.",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.AuthorizationError:
            self.logger.log(
                LoggerType.API,
                "Unauthorized - please check your credentials for %s at Landroid Cloud",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.ForbiddenError:
            self.logger.log(
                LoggerType.API,
                "Server rejected access for %s at Landroid Cloud - this might be "
                "temporary due to high numbers of API requests from this IP address.",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.NotFoundError:
            self.logger.log(
                LoggerType.API,
                "Endpoint for %s was not found.",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.TooManyRequestsError:
            self.logger.log(
                LoggerType.API,
                "Too many requests for %s at Landroid Cloud. IP address temporary banned.",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.InternalServerError:
            self.logger.log(
                LoggerType.API,
                "Internal server error happend for the request to %s at Landroid Cloud.",
                self.config["email"],
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.ServiceUnavailableError:
            self.logger.log(
                LoggerType.API,
                "Service at Landroid Cloud was unavailable.",
                log_level=LogLevel.ERROR,
            )
            return False
        except exceptions.APIException as ex:
            self.logger.log(
                LoggerType.API,
                "%s",
                ex,
                log_level=LogLevel.ERROR,
            )
            return False
