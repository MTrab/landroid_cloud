"""pyWorxCloud definition."""
import contextlib
import logging
import time

from ratelimit import RateLimitException, limits

from .const import MAX_WAIT
from .worxlandroidapi import *

_LOGGER = logging.getLogger(__name__)

# Valid states - some are missing as these haven't been identified yet
StateDict = {
    0: "Idle",
    1: "Home",
    2: "Start sequence",
    3: "Leaving home",
    4: "Follow wire",
    5: "Searching home",
    6: "Searching wire",
    7: "Mowing",
    8: "Lifted",
    9: "Trapped",
    10: "Blade blocked",
    11: "Debug",
    12: "Remote control",
    30: "Going home",
    31: "Zoning",
    32: "Cutting edge",
    33: "Searching area",
    34: "Pause",
}

# Valid error states
ErrorDict = {
    0: "No error",
    1: "Trapped",
    2: "Lifted",
    3: "Wire missing",
    4: "Outside wire",
    5: "Rain delay",
    6: "Close door to mow",
    7: "Close door to go home",
    8: "Blade motor blocked",
    9: "Wheel motor blocked",
    10: "Trapped timeout",
    11: "Upside down",
    12: "Battery low",
    13: "Reverse wire",
    14: "Charge error",
    15: "Timeout finding home",
    16: "Locked",
    17: "Battery temperature error",
    18: "dummy model",
    19: "Battery trunk open timeout",
    20: "wire sync",
    21: "msg num",
}

UNKNOWN_ERROR = "Unknown error (%s)"
POLL_LIMIT_PERIOD = 30  # s
POLL_CALLS_LIMIT = 1  # polls per timeframe


class WorxCloud:
    """Worx by Landroid Cloud connector."""

    wait = True

    def __init__(self, username: str, password: str, cloud_type: str = "worx"):
        """Define WorxCloud object."""
        self._worx_mqtt_client_id = ""
        self._worx_mqtt_endpoint = ""

        self._api = WorxLandroidAPI()

        self._api.username = username
        self._api.password = password
        self._api.type = (
            cloud_type  # Usable cloud_types are: worx, kress and landxcape.
        )

        self._raw = ""
        self._callback = None  # Callback used when data arrives from cloud

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
        import paho.mqtt.client as mqtt

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

        # if 'return_code' in auth_data:
        #     return False

        try:
            self._api.set_token(auth_data["access_token"])
            self._api.set_token_type(auth_data["token_type"])

            self._api.get_profile()
            profile = self._api.data
            if profile is None:
                return False
            self._worx_mqtt_endpoint = profile["mqtt_endpoint"]

            self._worx_mqtt_client_id = "android-" + self._api.uuid
        except:
            return False

    @contextlib.contextmanager
    def _get_cert(self):
        """Cet current certificate."""
        import base64

        certresp = self._api.get_cert()
        cert = base64.b64decode(certresp["pkcs12"])

        with pfx_to_pem(certresp["pkcs12"]) as pem_cert:
            yield pem_cert

    def _get_mac_address(self):
        """Get device MAC address for identification."""
        self._fetch()
        self.mqtt_out = self.mqtt_topics["command_out"]
        self.mqtt_in = self.mqtt_topics["command_in"]
        self.mac = self.mac_address

    def _forward_on_message(self, client, userdata, message):
        """MQTT callback method definition."""
        import json

        json_message = message.payload.decode("utf-8")
        self._decodeData(json_message)

        if self._callback is not None:
            self._callback()

    def update(self) -> None:
        """Retrive current device status."""
        status = self._api.get_status(self.serial_number)
        status = str(status).replace("'", '"')
        self._raw = status

        self._decodeData(status)

    def _decodeData(self, indata) -> None:
        """Decode incoming JSON data."""
        import json

        data = json.loads(indata)
        if "dat" in data:
            self.firmware = data["dat"]["fw"]
            self.mowing_zone = 0 if data["dat"]["lz"] == 8 else data["dat"]["lz"]
            self.rssi = data["dat"]["rsi"]
            self.status = data["dat"]["ls"]
            self.status_description = StateDict[data["dat"]["ls"]]
            self.error = data["dat"]["le"]

            # Translate error code to text
            if data["dat"]["le"] in ErrorDict:
                self.error_description = ErrorDict[data["dat"]["le"]]
            else:
                self.error_description = f"Unknown error"

            self.current_zone = data["dat"]["lz"]
            self.locked = data["dat"]["lk"]

            # Get battery info if available
            if "bt" in data["dat"]:
                self.battery_temperature = data["dat"]["bt"]["t"]
                self.battery_voltage = data["dat"]["bt"]["v"]
                self.battery_percent = data["dat"]["bt"]["p"]
                self.battery_charging = data["dat"]["bt"]["c"]
                self.battery_charge_cycle = data["dat"]["bt"]["nr"]
                if self.battery_charge_cycles_reset != None:
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
                if self.blade_work_time_reset != None:
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
                self.gps_latitude = None
                self.gps_longitude = None
                if "4G" in data["dat"]["modules"]:
                    self.gps_latitude = data["dat"]["modules"]["4G"]["gps"]["coo"][0]
                    self.gps_longitude = data["dat"]["modules"]["4G"]["gps"]["coo"][1]

            # Get remaining rain delay if available
            if "rain" in data["dat"]:
                self.rain_delay_time_remaining = data["dat"]["rain"]["cnt"]
                self.rain_sensor_triggered = (
                    True if str(data["dat"]["rain"]["s"]) == "1" else False
                )

        if "cfg" in data:
            self.updated = data["cfg"]["tm"] + " " + data["cfg"]["dt"]
            self.rain_delay = data["cfg"]["rd"]
            self.serial = data["cfg"]["sn"]

            # Fetch main schedule
            if "sc" in data["cfg"]:
                self.ots_enabled = True if "ots" in data["cfg"]["sc"] else False
                self.schedule_mower_active = (
                    True if str(data["cfg"]["sc"]["m"]) == "1" else False
                )
                self.partymode_enabled = (
                    True if str(data["cfg"]["sc"]["m"]) == "2" else False
                )
                self.partymode = True if "distm" in data["cfg"]["sc"] else False
                self.schedule_variation = data["cfg"]["sc"]["p"]
                self.schedule_day_sunday_start = data["cfg"]["sc"]["d"][0][0]
                self.schedule_day_sunday_duration = data["cfg"]["sc"]["d"][0][1]
                self.schedule_day_sunday_boundary = data["cfg"]["sc"]["d"][0][2]
                self.schedule_day_monday_start = data["cfg"]["sc"]["d"][1][0]
                self.schedule_day_monday_duration = data["cfg"]["sc"]["d"][1][1]
                self.schedule_day_monday_boundary = data["cfg"]["sc"]["d"][1][2]
                self.schedule_day_tuesday_start = data["cfg"]["sc"]["d"][2][0]
                self.schedule_day_tuesday_duration = data["cfg"]["sc"]["d"][2][1]
                self.schedule_day_tuesday_boundary = data["cfg"]["sc"]["d"][2][2]
                self.schedule_day_wednesday_start = data["cfg"]["sc"]["d"][3][0]
                self.schedule_day_wednesday_duration = data["cfg"]["sc"]["d"][3][1]
                self.schedule_day_wednesday_boundary = data["cfg"]["sc"]["d"][3][2]
                self.schedule_day_thursday_start = data["cfg"]["sc"]["d"][4][0]
                self.schedule_day_thursday_duration = data["cfg"]["sc"]["d"][4][1]
                self.schedule_day_thursday_boundary = data["cfg"]["sc"]["d"][4][2]
                self.schedule_day_friday_start = data["cfg"]["sc"]["d"][5][0]
                self.schedule_day_friday_duration = data["cfg"]["sc"]["d"][5][1]
                self.schedule_day_friday_boundary = data["cfg"]["sc"]["d"][5][2]
                self.schedule_day_saturday_start = data["cfg"]["sc"]["d"][6][0]
                self.schedule_day_saturday_duration = data["cfg"]["sc"]["d"][6][1]
                self.schedule_day_saturday_boundary = data["cfg"]["sc"]["d"][6][2]

            # Fetch secondary schedule
            if "dd" in data["cfg"]["sc"]:
                self.schedule_day_sunday_2_start = data["cfg"]["sc"]["dd"][0][0]
                self.schedule_day_sunday_2_duration = data["cfg"]["sc"]["dd"][0][1]
                self.schedule_day_sunday_2_boundary = data["cfg"]["sc"]["dd"][0][2]
                self.schedule_day_monday_2_start = data["cfg"]["sc"]["dd"][1][0]
                self.schedule_day_monday_2_duration = data["cfg"]["sc"]["dd"][1][1]
                self.schedule_day_monday_2_boundary = data["cfg"]["sc"]["dd"][1][2]
                self.schedule_day_tuesday_2_start = data["cfg"]["sc"]["dd"][2][0]
                self.schedule_day_tuesday_2_duration = data["cfg"]["sc"]["dd"][2][1]
                self.schedule_day_tuesday_2_boundary = data["cfg"]["sc"]["dd"][2][2]
                self.schedule_day_wednesday_2_start = data["cfg"]["sc"]["dd"][3][0]
                self.schedule_day_wednesday_2_duration = data["cfg"]["sc"]["dd"][3][1]
                self.schedule_day_wednesday_2_boundary = data["cfg"]["sc"]["dd"][3][2]
                self.schedule_day_thursday_2_start = data["cfg"]["sc"]["dd"][4][0]
                self.schedule_day_thursday_2_duration = data["cfg"]["sc"]["dd"][4][1]
                self.schedule_day_thursday_2_boundary = data["cfg"]["sc"]["dd"][4][2]
                self.schedule_day_friday_2_start = data["cfg"]["sc"]["dd"][5][0]
                self.schedule_day_friday_2_duration = data["cfg"]["sc"]["dd"][5][1]
                self.schedule_day_friday_2_boundary = data["cfg"]["sc"]["dd"][5][2]
                self.schedule_day_saturday_2_start = data["cfg"]["sc"]["dd"][6][0]
                self.schedule_day_saturday_2_duration = data["cfg"]["sc"]["dd"][6][1]
                self.schedule_day_saturday_2_boundary = data["cfg"]["sc"]["dd"][6][2]

        self.islocked = True if self.locked == 1 else False
        self.wait = False

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT callback method."""
        client.subscribe(self.mqtt_out)

    @limits(calls=POLL_CALLS_LIMIT, period=POLL_LIMIT_PERIOD)
    def _poll(self) -> None:
        """Force poll."""
        # DO NOT CALL TOO OFTEN AS YOU WILL GET BANNED!
        self._mqtt.publish(self.mqtt_in, '{"cmd":0}', qos=0, retain=False)

    def tryToPoll(self) -> None:
        """Try to issue a forced poll."""
        try:
            self._poll()
        except RateLimitException as exception:
            return f"The rate limit of {POLL_CALLS_LIMIT} status polls per {POLL_LIMIT_PERIOD} seconds has been exceeded. Please wait {round(exception.period_remaining)} seconds before polling again."

    def start(self) -> None:
        """Start mowing."""
        self._mqtt.publish(self.mqtt_in, '{"cmd":1}', qos=0, retain=False)

    def pause(self) -> None:
        """Pause mowing."""
        self._mqtt.publish(self.mqtt_in, '{"cmd":2}', qos=0, retain=False)

    def stop(self) -> None:
        """Stop (and go home)."""
        self._mqtt.publish(self.mqtt_in, '{"cmd":3}', qos=0, retain=False)

    def zonetraining(self) -> None:
        """Start zonetraining."""
        self._mqtt.publish(self.mqtt_in, '{"cmd":4}', qos=0, retain=False)

    def lock(self, enabled: bool) -> None:
        """Lock or Unlock device."""
        if enabled:
            self._mqtt.publish(self.mqtt_in, '{"cmd":5}', qos=0, retain=False)
        else:
            self._mqtt.publish(self.mqtt_in, '{"cmd":6}', qos=0, retain=False)

    def restart(self):
        """Reboot device."""
        self._mqtt.publish(self.mqtt_in, '{"cmd":7}', qos=0, retain=False)

    def setRainDelay(self, rainDelay) -> None:
        """Set new rain delay."""
        msg = '{"rd": %s}' % (rainDelay)
        self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)

    def enableSchedule(self, enable: bool) -> None:
        """Enable or disable schedule."""
        if enable:
            msg = '{"sc": {"m": 1}}'
            self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
        else:
            msg = '{"sc": {"m": 0}}'
            self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)

    def _fetch(self) -> None:
        """Fetch devices."""
        self._api.get_products()
        products = self._api.data

        for attr, val in products[self._dev_id].items():
            setattr(self, str(attr), val)

    def enumerate(self) -> int:
        """Enumerate amount of devices attached to account."""
        self._api.get_products()
        products = self._api.data
        return len(products)

    def sendData(self, data) -> None:
        """Publish data to the device."""
        if self.online:
            self._mqtt.publish(self.mqtt_in, data, qos=0, retain=False)

    def partyMode(self, enabled: bool) -> None:
        """Enable or disable Party Mode."""
        if self.online:
            if enabled:
                msg = '{"sc": {"m": 2, "distm": 0}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)
            else:
                msg = '{"sc": {"m": 1, "distm": 0}}'
                self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)

    def setZone(self, zone) -> None:
        """Set next zone to mow."""
        if self.online:
            msg = '{"lz":' + zone + "}"
            self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)

    def startEdgecut(self) -> None:
        """Start edgecut routine."""
        if self.online:
            msg = '{"sc":{"ots":{"bc":1,"wtm":0}}}'
            self._mqtt.publish(self.mqtt_in, msg, qos=0, retain=False)


@contextlib.contextmanager
def pfx_to_pem(pfx_data):
    """Decrypts the .pfx file to be used with requests."""
    """ Based on https://gist.github.com/erikbern/756b1d8df2d1487497d29b90e81f8068 """
    import base64
    import tempfile

    import OpenSSL.crypto

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
        ca = p12.get_ca_certificates()
        if ca is not None:
            for cert in ca:
                f_pem.write(
                    OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
                )
        f_pem.close()
        yield t_pem.name
