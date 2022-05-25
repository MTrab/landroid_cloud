"""pyWorxCloud definition."""
from __future__ import annotations

import json
import base64
import logging
import tempfile
import contextlib
import time
import paho.mqtt.client as mqtt
import OpenSSL.crypto

from .day_map import DAY_MAP
from .exceptions import NoOneTimeScheduleError, NoPartymodeError, OfflineError
from .landroidapi import LandroidAPI
from .schedules import Schedule, ScheduleType, TYPE_MAP

_LOGGER = logging.getLogger(__name__)


class WorxCloud:
    """Worx by Landroid Cloud connector."""

    wait = True

    def __init__(self, username: str, password: str, cloud_type: str = "worx") -> None:
        """Define WorxCloud object."""
        self._worx_mqtt_client_id = None
        self._worx_mqtt_endpoint = None

        self._api = LandroidAPI()

        self._api.password = password
        self._api.type = (
            cloud_type  # Usable cloud_types are: worx, kress and landxcape.
        )
        self._api.username = username

        self._auth_result = False
        self._callback = None  # Callback used when data arrives from cloud
        self._dev_id = None
        self._mqtt = None
        self._raw = None
        self._save_zones = None

        self.accessories = None
        self.battery_charge_cycle = None
        self.battery_charge_cycle_current = None
        self.battery_charge_cycles_reset = None
        self.battery_charging = None
        self.battery_percent = 0
        self.battery_temperature = 0
        self.battery_voltage = 0
        self.blade_time = 0
        self.blade_time_current = 0
        self.blade_work_time_reset = None
        self.board = None
        self.current_zone = 0
        self.distance = 0
        self.error = None
        self.error_description = None
        self.firmware = None
        self.gps_latitude = None
        self.gps_longitude = None
        self.locked = False
        self.mac = None
        self.mac_address = None
        self.mowing_zone = 0
        self.mqtt_in = None
        self.mqtt_out = None
        self.mqtt_topics = {}
        self.online = False
        self.ots_capable = False
        self.partymode_capable = False
        self.partymode_enabled = False
        self.pitch = 0
        self.rain_delay = None
        self.rain_delay_time_remaining = None
        self.rain_sensor_triggered = None
        self.roll = 0
        self.rssi = None
        self.schedule_mower_active = False
        self.schedule_variation = None
        self.schedules = {}
        self.serial = None
        self.serial_number = None
        self.status = None
        self.status_description = None
        self.updated = None
        self.work_time = 0
        self.yaw = 0
        self.zone = []
        self.zone_probability = []

    def initialize(self) -> bool:
        """Initialize current object."""
        auth = self._authenticate()
        if auth is False:
            self._auth_result = False
            return False

        self._auth_result = True

        return True

    def set_callback(self, callback) -> None:
        """Set callback function to call when data arrives from cloud."""
        self._callback = callback

    def connect(self, dev_id: int, verify_ssl: bool = True) -> bool:
        """Connect to cloud services."""
        self._dev_id = dev_id
        self._get_mac_address()

        self._mqtt = mqtt.Client(self._worx_mqtt_client_id, protocol=mqtt.MQTTv311)

        self._mqtt.on_message = self._forward_on_message
        self._mqtt.on_connect = self._on_connect

        try:
            with self._get_cert() as cert:
                self._mqtt.tls_set(certfile=cert)
        except ValueError:
            pass

        if not verify_ssl:
            self._mqtt.tls_insecure_set(True)

        conn_res = self._mqtt.connect(
            self._worx_mqtt_endpoint, port=8883, keepalive=600
        )
        if conn_res:
            return False

        self._mqtt.loop_start()
        mqp = self._mqtt.publish(self.mqtt_in, "{}", qos=0, retain=False)
        while not mqp.is_published:
            time.sleep(0.1)

        return True

    @property
    def auth_result(self) -> bool:
        """Return current authentication result."""
        return self._auth_result

    def _authenticate(self):
        """Authenticate the user."""
        auth_data = self._api.auth()

        try:
            self._api.set_token(auth_data["access_token"])
            self._api.set_token_type(auth_data["token_type"])

            self._api.get_profile()
            profile = self._api.data
            if profile is None:
                return False
            self._worx_mqtt_endpoint = profile["mqtt_endpoint"]

            self._worx_mqtt_client_id = "android-" + self._api.uuid
        except:  # pylint: disable=bare-except
            return False

    @contextlib.contextmanager
    def _get_cert(self):
        """Cet current certificate."""

        certresp = self._api.get_cert()

        with pfx_to_pem(certresp["pkcs12"]) as pem_cert:
            yield pem_cert

    def _get_mac_address(self):
        """Get device MAC address for identification."""
        self._fetch()
        self.mqtt_out = self.mqtt_topics["command_out"]
        self.mqtt_in = self.mqtt_topics["command_in"]
        self.mac = self.mac_address
        self.board = self.mqtt_out.split("/")[0]

    def _forward_on_message(
        self, client, userdata, message
    ):  # pylint: disable=unused-argument
        """MQTT callback method definition."""
        json_message = message.payload.decode("utf-8")
        self._decode_data(json_message)

        if self._callback is not None:
            self._callback()

    def update(self) -> None:
        """Retrive current device status."""
        status = self._api.get_status(self.serial_number)
        status = str(status).replace("'", '"')
        self._raw = status

        self._decode_data(status)

    def _decode_data(self, indata) -> None:
        """Decode incoming JSON data."""
        data = json.loads(indata)
        if "dat" in data:
            self.firmware = data["dat"]["fw"]
            self.mowing_zone = data["dat"]["lz"]
            self.rssi = data["dat"]["rsi"]
            self.status = data["dat"]["ls"]
            self.error = data["dat"]["le"]

            self.current_zone = data["dat"]["lz"]
            self.locked = bool(data["dat"]["lk"])

            # Get battery info if available
            if "bt" in data["dat"]:
                self.battery_temperature = data["dat"]["bt"]["t"]
                self.battery_voltage = data["dat"]["bt"]["v"]
                self.battery_percent = data["dat"]["bt"]["p"]
                self.battery_charging = data["dat"]["bt"]["c"]
                self.battery_charge_cycle = data["dat"]["bt"]["nr"]
                if self.battery_charge_cycles_reset is not None:
                    self.battery_charge_cycle_current = (
                        self.battery_charge_cycle - self.battery_charge_cycles_reset
                    )
                    if self.battery_charge_cycle_current < 0:
                        self.battery_charge_cycle_current = 0
                else:
                    self.battery_charge_cycle_current = self.battery_charge_cycle

            # Get blade data if available
            if "st" in data["dat"]:
                self.blade_time = data["dat"]["st"]["b"]
                if self.blade_work_time_reset is not None:
                    self.blade_time_current = (
                        self.blade_time - self.blade_work_time_reset
                    )
                    if self.blade_time_current < 0:
                        self.blade_time_current = 0
                else:
                    self.blade_time_current = self.blade_time
                self.distance = data["dat"]["st"]["d"]
                self.work_time = data["dat"]["st"]["wt"]

            # Get orientation if available.
            if "dmp" in data["dat"]:
                self.pitch = data["dat"]["dmp"][0]
                self.roll = data["dat"]["dmp"][1]
                self.yaw = data["dat"]["dmp"][2]

            # Check for extra module availability
            if "modules" in data["dat"]:
                if "4G" in data["dat"]["modules"]:
                    self.gps_latitude = data["dat"]["modules"]["4G"]["gps"]["coo"][0]
                    self.gps_longitude = data["dat"]["modules"]["4G"]["gps"]["coo"][1]

            # Get remaining rain delay if available
            if "rain" in data["dat"]:
                self.rain_delay_time_remaining = data["dat"]["rain"]["cnt"]
                self.rain_sensor_triggered = bool(str(data["dat"]["rain"]["s"]) == "1")

        if "cfg" in data:
            self.updated = data["cfg"]["tm"] + " " + data["cfg"]["dt"]
            self.rain_delay = data["cfg"]["rd"]
            self.serial = data["cfg"]["sn"]

            # Fetch zone information
            if "mz" in data["cfg"]:
                self.zone = data["cfg"]["mz"]
                self.zone_probability = data["cfg"]["mzv"]

            # Fetch main schedule
            if "sc" in data["cfg"]:
                self.ots_capable = bool("ots" in data["cfg"]["sc"])
                self.schedule_mower_active = bool(str(data["cfg"]["sc"]["m"]) == "1")
                self.partymode_enabled = bool(str(data["cfg"]["sc"]["m"]) == "2")
                self.partymode_capable = bool("distm" in data["cfg"]["sc"])

                self.schedule_variation = data["cfg"]["sc"]["p"]

                sch_type = ScheduleType.PRIMARY
                schedule = Schedule(sch_type).todict
                self.schedules[TYPE_MAP[sch_type]] = schedule["days"]

                for day in range(0, len(data["cfg"]["sc"]["d"])):
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["start"] = data[
                        "cfg"
                    ]["sc"]["d"][day][0]
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["duration"] = data[
                        "cfg"
                    ]["sc"]["d"][day][1]
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["boundary"] = bool(
                        data["cfg"]["sc"]["d"][day][2]
                    )

            # Fetch secondary schedule
            if "dd" in data["cfg"]["sc"]:
                sch_type = ScheduleType.SECONDARY
                schedule = Schedule(sch_type).todict
                self.schedules[TYPE_MAP[sch_type]] = schedule["days"]

                for day in range(0, len(data["cfg"]["sc"]["d"])):
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["start"] = data[
                        "cfg"
                    ]["sc"]["dd"][day][0]
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["duration"] = data[
                        "cfg"
                    ]["sc"]["dd"][day][1]
                    self.schedules[TYPE_MAP[sch_type]][DAY_MAP[day]]["boundary"] = bool(
                        data["cfg"]["sc"]["dd"][day][2]
                    )

        self.wait = False

    def _on_connect(
        self, client, userdata, flags, rc
    ):  # pylint: disable=unused-argument,invalid-name
        """MQTT callback method."""
        client.subscribe(self.mqtt_out)

    def start(self) -> None:
        """Start mowing."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, '{"cmd":1}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def pause(self) -> None:
        """Pause mowing."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, '{"cmd":2}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def home(self) -> None:
        """Stop (and go home)."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, '{"cmd":3}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def zonetraining(self) -> None:
        """Start zonetraining."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, '{"cmd":4}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def lock(self, enabled: bool) -> None:
        """Lock or Unlock device."""
        if self.online:
            if enabled:
                self._mqtt.publish(self.mqtt_in, '{"cmd":5}', qos=0, retain=False)
            else:
                self._mqtt.publish(self.mqtt_in, '{"cmd":6}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def restart(self):
        """Reboot device."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, '{"cmd":7}', qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def raindelay(self, rain_delay) -> None:
        """Set new rain delay."""
        if self.online:
            msg = f'"rd": {rain_delay}'
            self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def schedule(self, enable: bool) -> None:
        """Enable or disable schedule."""
        if self.online:
            if enable:
                msg = '{"sc": {"m": 1}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
            else:
                msg = '{"sc": {"m": 0}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def _fetch(self) -> None:
        """Fetch devices."""
        self._api.get_products()
        products = self._api.data

        accessories = None
        for attr, val in products[self._dev_id].items():
            if attr == "accessories":
                accessories = val
            else:
                setattr(self, str(attr), val)

        if not accessories is None:
            self.accessories = []
            for key in accessories:
                self.accessories.append(key)

    def enumerate(self) -> int:
        """Enumerate amount of devices attached to account."""
        self._api.get_products()
        products = self._api.data
        return len(products)

    def send(self, data) -> None:
        """Publish data to the device."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, data, qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def enable_partymode(self, enabled: bool) -> None:
        """Enable or disable Party Mode."""
        if self.online and self.partymode_capable:
            if enabled:
                msg = '{"sc": {"m": 2, "distm": 0}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
            else:
                msg = '{"sc": {"m": 1, "distm": 0}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
        elif not self.partymode_capable:
            raise NoPartymodeError("This device does not support Partymode")
        elif not self.online:
            raise OfflineError("The device is currently offline, no action was sent.")

    def ots(self, boundary: bool, runtime: str | int) -> None:
        """Start OTS routine."""
        if self.online and self.ots_capable:
            if not isinstance(runtime, int):
                runtime = int(runtime)

            raw = {"sc": {"ots": {"bc": int(boundary), "wtm": runtime}}}
            _LOGGER.debug(json.dumps(raw))
            self._mqtt.publish(self.mqtt_in, json.dumps(raw), qos=0, retain=False)
        elif not self.ots_capable:
            raise NoOneTimeScheduleError(
                "This device does not support Edgecut-on-demand"
            )
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    def setzone(self, zone: str | int) -> None:
        """Set next zone to mow."""
        if self.online:
            if not isinstance(zone, int):
                zone = int(zone)
            current = self.zone_probability

            new_zones = current
            while not new_zones[self.mowing_zone] == zone:
                tmp = []
                tmp.append(new_zones[9])
                for i in range(0, 9):
                    tmp.append(new_zones[i])
                new_zones = tmp

            raw = {"mzv": new_zones}
            self._mqtt.publish(self.mqtt_in, json.dumps(raw), qos=0, retain=False)
        else:
            raise OfflineError("The device is currently offline, no action was sent.")

    # def edgecut(self) -> None:
    #     """Start edgecut routine."""
    #     if self.online and self.ots_capable:
    #         msg = '{"sc":{"ots":{"bc":1,"wtm":0}}}'
    #         self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
    #     elif not self.ots_capable:
    #         raise NoOneTimeScheduleError(
    #             "This device does not support Edgecut-on-demand"
    #         )
    #     elif not self.online:
    #         raise OfflineError("The device is currently offline, no action was sent.")


@contextlib.contextmanager
def pfx_to_pem(pfx_data):
    """Decrypts the .pfx file to be used with requests."""
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as t_pem:
        f_pem = open(t_pem.name, "wb")
        p12 = OpenSSL.crypto.load_pkcs12(base64.b64decode(pfx_data), "")
        f_pem.write(
            OpenSSL.crypto.dump_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()
            )
        )
        f_pem.write(
            OpenSSL.crypto.dump_certificate(
                OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()
            )
        )
        certauth = p12.get_ca_certificates()
        if certauth is not None:
            for cert in certauth:
                f_pem.write(
                    OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
                )
        f_pem.close()
        yield t_pem.name
