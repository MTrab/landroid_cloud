"""Support for Worx Landroid Cloud based lawn mowers."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_DEVICE,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import slugify as util_slugify

_LOGGER = logging.getLogger(__name__)

DEFAULT_VERIFY_SSL = True
DEFAULT_NAME = "landroid"
DOMAIN = "landroid_cloud"
LANDROID_API = "landroid_cloud_api"
SCAN_INTERVAL = timedelta(seconds=60)
UPDATE_SIGNAL = "landroid_cloud_update_signal"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN:vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_EMAIL): cv.string,
                        vol.Required(CONF_PASSWORD): cv.string,
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_START = "start"
SERVICE_PAUSE = "pause"
SERVICE_HOME = "home"
SERVICE_CONFIG = "config"


API_WORX_SENSORS = {
    "battery": {
        "state": {
            "battery_percent": "state",
            "battery_voltage": "battery_voltage",
            "battery_temperature": "battery_temperature",
            "battery_charge_cycles": "charge_cycles",
            "battery_charging": "charging",
        },
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": None,
    },
    "error": {
        "state": {"error_description": "state", "error": "error_id"},
        "icon": None,
        "unit": None,
        "device_class": None,
    },
    "status": {
        "state": {
            "id": "id",
            "status_description": "state",
            "blade_time": "blade_time",
            "work_time": "work_time",
            "distance": "distance",
            "status": "status_id",
            "updated": "last_update",
            "rssi": "rssi",
            "yaw": "yaw",
            "roll": "roll",
            "pitch": "pitch",
        },
        "icon": None,
        "unit": None,
        "device_class": None,
    },
}

client = []

async def async_setup(hass, config):
    """Set up the Worx Landroid Cloud component."""
    import pyworxcloud
    hass.data[LANDROID_API] = {}
    dev = 0

    for cloud in config[DOMAIN]:
        cloud_email = cloud[CONF_EMAIL]
        cloud_password = cloud[CONF_PASSWORD]

        master = pyworxcloud.WorxCloud()
        auth = await master.initialize(cloud_email, cloud_password)

        if not auth:
            _LOGGER.warning("Error in authentication!")
            return False

        num_dev = master.enumerate()

        for device in range(num_dev):
            client.append(dev)
            _LOGGER.debug("Connecting to device ID %s (%s)", device, cloud_email)
            client[dev] = pyworxcloud.WorxCloud()
            await client[dev].initialize(cloud_email, cloud_password)
            await client[dev].connect(device, False)

            api = WorxLandroidAPI(hass, dev, client[dev], config)
            async_track_time_interval(hass, api.async_update, SCAN_INTERVAL)
            hass.data[LANDROID_API][dev] = api
            dev += 1

    async def handle_start(call):
        """Handle start service call."""
        if "id" in call.data:
            ID = call.data["id"]

            for cli in client:
                attrs = vars(cli)
                if (attrs["id"] == ID):
                    cli.start()
        else:
            client[0].start()

    hass.services.async_register(DOMAIN, SERVICE_START, handle_start)

    async def handle_pause(call):
        """Handle pause service call."""
        if "id" in call.data:
            ID = call.data["id"]

            for cli in client:
                attrs = vars(cli)
                if (attrs["id"] == ID):
                    cli.pause()
        else:
            client[0].pause()

    hass.services.async_register(DOMAIN, SERVICE_PAUSE, handle_pause)

    async def handle_home(call):
        """Handle pause service call."""
        if "id" in call.data:
            ID = call.data["id"]

            for cli in client:
                attrs = vars(cli)
                if (attrs["id"] == ID):
                    cli.stop()
        else:
            client[0].stop()

    hass.services.async_register(DOMAIN, SERVICE_HOME, handle_home)

#    async def handle_config(call):
#        """Handle config service call."""
#        if "id" in call.data:
#            _LOGGER.debug("Data from Home Assistant: %s", call.data["id"])
#
#            for cli in client:
#                attrs = vars(cli)
#                if (attrs["id"] == call.data["id"]):
#                    _LOGGER.debug(attrs["name"])
#        else:
#            _LOGGER.debug("No ID present - using 0")
#
#    hass.services.async_register(DOMAIN, SERVICE_CONFIG, handle_config)

    return True


class WorxLandroidAPI:
    """Handle the API calls."""

    def __init__(self, hass, device, client, config):
        """Set up instance."""
        self._hass = hass
        self._client = client
        self._device = device
        self.config = config

        sensor_info = []
        info = {}
        info["name"] = util_slugify(f"{DEFAULT_NAME}_{self._client.name}")
        info["friendly"] = self._client.name
        info["id"] = self._device
        sensor_info.append(info)

        load_platform(self._hass, "sensor", DOMAIN, sensor_info, self.config)

    def get_data(self, sensor_type):
        """Get data from state cache."""
        methods = API_WORX_SENSORS[sensor_type]
        data = {}
        for prop, attr in methods["state"].items():
            if hasattr(self._client, prop):
                prop_data = getattr(self._client, prop)
                data[attr] = prop_data
        return data

    async def async_update(self, now=None):
        """Update the state cache from Landroid API."""
        dispatcher_send(self._hass, UPDATE_SIGNAL)
