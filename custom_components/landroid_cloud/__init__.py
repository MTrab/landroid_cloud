"""Support for Worx Landroid Cloud based lawn mowers."""
import json
import logging
import time
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import pyworxcloud
import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import slugify as util_slugify

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    LANDROID_API,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_HOME,
    SERVICE_LOCK,
    SERVICE_PARTYMODE,
    SERVICE_PAUSE,
    SERVICE_POLL,
    SERVICE_RESTART,
    SERVICE_SETZONE,
    SERVICE_START,
    UPDATE_SIGNAL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_VERIFY_SSL = True
SCAN_INTERVAL = timedelta(seconds=30)
FORCED_UPDATE = timedelta(minutes=30)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_EMAIL): cv.string,
                        vol.Required(CONF_PASSWORD): cv.string,
                        vol.Optional(CONF_TYPE): cv.string,
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)


API_WORX_SENSORS = {
    "battery": {
        "state": {
            "battery_percent": "state",
            "battery_voltage": "battery_voltage",
            "battery_temperature": "battery_temperature",
            "battery_charge_cycle": "total_charge_cycles",
            "battery_charge_cycle_current": "current_charge_cycles",
            "battery_charge_cycles_reset_at": "charge_cycles_reset",
            "battery_charging": "charging",
        },
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": "battery",
    },
    "error": {
        "state": {"error_description": "state", "error": "error_id"},
        "icon": "mdi:alert",
        "unit": None,
        "device_class": None,
    },
    "status": {
        "state": {
            "id": "id",
            "status_description": "state",
            "blade_time": "total_blade_time",
            "blade_time_current": "current_blade_time",
            "blade_work_time_reset_at": "blade_time_reset",
            "work_time": "work_time",
            "distance": "distance",
            "status": "status_id",
            "updated": "last_update",
            "rssi": "rssi",
            "yaw": "yaw",
            "roll": "roll",
            "pitch": "pitch",
            "gps_latitude": "latitude",
            "gps_longitude": "longitude",
            "rain_delay": "raindelay",
            "schedule_variation": "timeextension",
            "firmware": "firmware_version",
            "serial": "serial",
            "mac": "mac",
            "schedule_mower_active": "schedule_enabled",
            "partymode_enabled": "partymode_enabled",
            "mowing_zone": "mowing_zone",
            "accessories": "accessories",
            "islocked": "locked",
        },
        "icon": None,
        "unit": None,
        "device_class": None,
    },
}

client = []

def check_id(data):
    if "id" in data and data["id"] is not None:
        return True
    else:
        return False

async def async_setup(hass, config):
    """Set up the Worx Landroid Cloud component."""

    hass.data[LANDROID_API] = {}
    dev = 0
    partymode = False
    ots = False

    for cloud in config[DOMAIN]:
        cloud_email = cloud[CONF_EMAIL]
        cloud_password = cloud[CONF_PASSWORD]
        cloud_type = cloud.get(CONF_TYPE, "worx")

        master = pyworxcloud.WorxCloud()
        auth = await hass.async_add_executor_job(
            master.initialize, cloud_email, cloud_password, cloud_type
        )

        if not auth:
            _LOGGER.warning("Error in authentication!")
            return False

        try:
            num_dev = await hass.async_add_executor_job(master.enumerate)
        except Exception as err:
            _LOGGER.warning(err)
            return False

        for device in range(num_dev):
            client.append(dev)
            _LOGGER.debug("Connecting to device ID %s (%s)", device, cloud_email)
            client[dev] = pyworxcloud.WorxCloud()
            await hass.async_add_executor_job(
                client[dev].initialize, cloud_email, cloud_password, cloud_type
            )
            await hass.async_add_executor_job(client[dev].connect, device, False)

            api = WorxLandroidAPI(hass, dev, client[dev], config)
            await api.async_force_update()
            async_track_time_interval(hass, api.async_update, SCAN_INTERVAL)
            async_track_time_interval(hass, api.async_force_update, FORCED_UPDATE)
            hass.data[LANDROID_API][dev] = api
            if not hasattr(client[dev], "partymode"):
                partymode = False
            elif not partymode and client[dev].partymode:
                _LOGGER.debug("Partymode available: %s", client[dev].partymode)
                partymode = True
            if not hasattr(client[dev], "ots_enabled"):
                ots = False
            elif not ots and client[dev].ots_enabled:
                _LOGGER.debug("OTS enabled: %s", client[dev].ots_enabled)
                ots = True
            dev += 1

    async def handle_poll(call):
        """Handle poll service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    error = cli.tryToPoll()
                    if error is not None:
                        _LOGGER.warning(error)
                    elif error is None:
                        _LOGGER.debug("Poll successful - updating info")
                        await hass.async_add_executor_job(cli.getStatus)

        else:
            error = client[0].tryToPoll()
            if error is not None:
                _LOGGER.warning(error)
            elif error is None:
                _LOGGER.debug("Poll successful - updating info")
                await hass.async_add_executor_job(client[0].getStatus)

    hass.services.async_register(DOMAIN, SERVICE_POLL, handle_poll)

    async def handle_poll(call):
        """Handle poll service call."""
        if check_id(call.data):
            ID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == ID:
                    error = cli.tryToPoll()
                    if error is not None:
                        _LOGGER.warning(error)

        else:
            error = client[0].tryToPoll()
            if error is not None:
                _LOGGER.warning(error)

    hass.services.async_register(DOMAIN, SERVICE_POLL, handle_poll)

    async def handle_start(call):
        """Handle start service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.start()
        else:
            client[0].start()

    hass.services.async_register(DOMAIN, SERVICE_START, handle_start)

    async def handle_pause(call):
        """Handle pause service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.pause()
        else:
            client[0].pause()

    hass.services.async_register(DOMAIN, SERVICE_PAUSE, handle_pause)

    async def handle_home(call):
        """Handle pause service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.stop()
        else:
            client[0].stop()

    hass.services.async_register(DOMAIN, SERVICE_HOME, handle_home)

    async def handle_config(call):
        """Handle config service call."""
        id = 0
        sendData = False
        tmpdata = {}

        if check_id(call.data):
            _LOGGER.debug("Data from Home Assistant: %s", call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == int(call.data["id"]):
                    break
                else:
                    id += 1

        if "raindelay" in call.data:
            tmpdata["rd"] = int(call.data["raindelay"])
            _LOGGER.debug(
                "Setting rain_delay for %s to %s",
                client[id].name,
                call.data["raindelay"],
            )
            sendData = True

        if "timeextension" in call.data:
            tmpdata["sc"] = {}
            tmpdata["sc"]["p"] = int(call.data["timeextension"])
            data = json.dumps(tmpdata)
            _LOGGER.debug(
                "Setting time_extension for %s to %s",
                client[id].name,
                call.data["timeextension"],
            )
            sendData = True

        if "multizone_distances" in call.data:
            tmpdata["mz"] = [int(x) for x in call.data["multizone_distances"]]
            data = json.dumps(tmpdata)
            _LOGGER.debug(
                "Setting multizone distances for %s to %s",
                client[id].name,
                call.data["multizone_distances"],
            )
            sendData = True

        if "multizone_probabilities" in call.data:
            tmpdata["mzv"] = []
            for idx, val in enumerate(call.data["multizone_probabilities"]):
                for _ in range(val):
                    tmpdata["mzv"].append(idx)
            data = json.dumps(tmpdata)
            _LOGGER.debug(
                "Setting multizone probabilities for %s to %s",
                client[id].name,
                call.data["multizone_probabilities"],
            )
            sendData = True

        if sendData:
            data = json.dumps(tmpdata)
            _LOGGER.debug("Sending: %s", data)
            client[id].sendData(data)

    hass.services.async_register(DOMAIN, SERVICE_CONFIG, handle_config)

    async def handle_partymode(call):
        """Handle partymode service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.partyMode(call.data["enable"])
        else:
            client[0].partyMode(call.data["enable"])

    if partymode:
        hass.services.async_register(DOMAIN, SERVICE_PARTYMODE, handle_partymode)

    async def handle_setzone(call):
        """Handle setzone service call."""
        zone = call.data["zone"]

        if not type(zone) == str:
            zone = str(zone)

        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.setZone(call.data["zone"])
        else:
            client[0].setZone(call.data["zone"])

    hass.services.async_register(DOMAIN, SERVICE_SETZONE, handle_setzone)

    async def handle_lock(call):
        """Handle lock service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.lock(call.data["enable"])
        else:
            client[0].lock(call.data["enable"])

    hass.services.async_register(DOMAIN, SERVICE_LOCK, handle_lock)

    async def handle_restart(call):
        """Handle restart service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.restart()
        else:
            client[0].restart()

    hass.services.async_register(DOMAIN, SERVICE_RESTART, handle_restart)

    async def handle_edgecut(call):
        """Handle restart service call."""
        if check_id(call.data):
            devID = int(call.data["id"])

            for cli in client:
                attrs = vars(cli)
                if attrs["id"] == devID:
                    cli.startEdgecut()
        else:
            client[0].startEdgecut()

    if ots:
        hass.services.async_register(DOMAIN, SERVICE_EDGECUT, handle_edgecut)

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
        # await self._hass.async_add_executor_job(self._client.getStatus)
        dispatcher_send(self._hass, UPDATE_SIGNAL)

    async def async_force_update(self, now=None):
        """Try forcing update."""
        _LOGGER.debug("Forcing update for %s", self._client.name)
        await self._hass.async_add_executor_job(self._client.getStatus)
