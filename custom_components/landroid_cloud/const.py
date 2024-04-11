"""Constants used by Landroid Cloud integration."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import IntEnum

from homeassistant.backports.enum import StrEnum
from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.const import STATE_IDLE, STATE_LOCKED, STATE_UNKNOWN
from pyworxcloud.clouds import CloudType
from pyworxcloud.utils import DeviceCapability

from .utils.logger import LogLevel

# Startup banner
STARTUP = """
-------------------------------------------------------------------
Landroid Cloud integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/landroid_cloud/issues
-------------------------------------------------------------------
"""

# Some defaults
DEFAULT_NAME = "landroid"
DOMAIN = "landroid_cloud"
PLATFORMS_SECONDARY = []
PLATFORMS_PRIMARY = ["lawn_mower", "sensor", "switch", "binary_sensor", "select"]
UPDATE_SIGNAL = "landroid_cloud_update"
LOGLEVEL = LogLevel.DEBUG
ENTITY_ID_FORMAT = DOMAIN + ".{}"

# Redact consts
REDACT_TITLE = "title"

# Service consts
SERVICE_CONFIG = "config"
SERVICE_PARTYMODE = "partymode"
SERVICE_SETZONE = "setzone"
SERVICE_LOCK = "lock"
SERVICE_RESTART = "restart"
SERVICE_EDGECUT = "edgecut"
SERVICE_OTS = "ots"
SERVICE_SCHEDULE = "schedule"
SERVICE_SEND_RAW = "send_raw"
SERVICE_TORQUE = "torque"

# Extra states
STATE_BATTERY_LOW = "battery_low"
STATE_BATTERY_OPEN = "battery_trunk_open_timeout"
STATE_BATTERY_TEMPERATURE_ERROR = "battery_temperature_error"
STATE_BLADE_BLOCKED = "blade_motor_blocked"
STATE_CAMERA_ERROR = "camera_error"
STATE_CHARGING_ERROR = "charge_error"
STATE_CLOSE_DOOR_HOME = "close_door_to_go_home"
STATE_CLOSE_DOOR_MOW = "close_door_to_mow"
STATE_DOCKING_ERROR = "charging_station_docking_error"
STATE_EDGECUT = "edgecut"
STATE_ESCAPED_DIGITAL_FENCE = "escaped_digital_fence"
STATE_EXESSIVE_SLOPE = "excessive_slope"
STATE_HEADLIGHT_ERROR = "headlight_error"
STATE_HEIGHT_BLOCKED = "blade_height_adjustment_blocked"
STATE_HBI_ERROR = "hbi_error"
STATE_INITIALIZING = "initializing"
STATE_INSUFFICIENT_SENSOR_DATA = "insufficient_sensor_data"
STATE_LIFTED = "lifted"
STATE_MAP_ERROR = "map_error"
STATE_MAPPING_FAILED = "mapping_exploration_failed"
STATE_MAPPING_REQUIRED = "mapping_exploration_required"
STATE_MISSING_DOCK = "missing_charging_station"
STATE_NO_ERROR = "no_error"
STATE_OFFLINE = "offline"
STATE_OTA_ERROR = "ota_error"
STATE_OUTSIDE_WIRE = "outside_wire"
STATE_RAINDELAY = "rain_delay"
STATE_RETURNING = "returning"
STATE_REVERSE_WIRE = "reverse_wire"
STATE_RFID_ERROR = "rfid_reader_error"
STATE_SEARCHING_ZONE = "searching_zone"
STATE_STARTING = "starting"
STATE_TIMEOUT_HOME = "timeout_finding_home"
STATE_TRAINING_START_DISALLOWED = "training_start_disallowed"
STATE_TRAPPED = "trapped"
STATE_TRAPPED_TIMEOUT = "trapped_timeout"
STATE_UNREACHABLE_DOCK = "unreachable_charging_station"
STATE_UNREACHABLE_ZONE = "unreachable_zone"
STATE_UPSIDE_DOWN = "upside_down"
STATE_ZONING = "zoning"
STATE_WHEEL_BLOCKED = "wheel_motor_blocked"
STATE_WIRE_MISSING = "wire_missing"
STATE_WIRE_SYNC = "wire_sync"


# Service attributes
ATTR_MULTIZONE_DISTANCES = "multizone_distances"
ATTR_MULTIZONE_PROBABILITIES = "multizone_probabilities"
ATTR_RAINDELAY = "raindelay"
ATTR_TIMEEXTENSION = "timeextension"
ATTR_ZONE = "zone"
ATTR_BOUNDARY = "boundary"
ATTR_JSON = "json"
ATTR_RUNTIME = "runtime"
ATTR_TORQUE = "torque"
ATTR_SERVICES = "services"
ATTR_SERVICE = "service"

# Attributes used for managing schedules
ATTR_TYPE = "type"
ATTR_MONDAY_START = "monday_start"
ATTR_MONDAY_END = "monday_end"
ATTR_MONDAY_BOUNDARY = "monday_boundary"
ATTR_TUESDAY_START = "tuesday_start"
ATTR_TUESDAY_END = "tuesday_end"
ATTR_TUESDAY_BOUNDARY = "tuesday_boundary"
ATTR_WEDNESDAY_START = "wednesday_start"
ATTR_WEDNESDAY_END = "wednesday_end"
ATTR_WEDNESDAY_BOUNDARY = "wednesday_boundary"
ATTR_THURSDAY_START = "thursday_start"
ATTR_THURSDAY_END = "thursday_end"
ATTR_THURSDAY_BOUNDARY = "thursday_boundary"
ATTR_FRIDAY_START = "friday_start"
ATTR_FRIDAY_END = "friday_end"
ATTR_FRIDAY_BOUNDARY = "friday_boundary"
ATTR_SATURDAY_START = "saturday_start"
ATTR_SATURDAY_END = "saturday_end"
ATTR_SATURDAY_BOUNDARY = "saturday_boundary"
ATTR_SUNDAY_START = "sunday_start"
ATTR_SUNDAY_END = "sunday_end"
ATTR_SUNDAY_BOUNDARY = "sunday_boundary"

# Entity extra attributes
ATTR_ACCESSORIES = "accessories"
ATTR_BATTERY = "battery"
ATTR_BLADES = "blades"
ATTR_CAPABILITIES = "capabilities"
ATTR_ERROR = "error"
ATTR_FIRMWARE = "firmware"
ATTR_LANDROIDFEATURES = "supported_landroid_features"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_LAWN = "lawn"
ATTR_MACADDRESS = "mac_address"
ATTR_MQTTCONNECTED = "mqtt_connected"
ATTR_ONLINE = "online"
ATTR_ORIENTATION = "orientation"
ATTR_RAINSENSOR = "rain_sensor"
ATTR_REGISTERED = "registered_at"
ATTR_SCHEDULE = "schedule"
ATTR_SERIAL = "serial_number"
ATTR_STATISTICS = "statistics"
ATTR_TIMEZONE = "time_zone"
ATTR_UPDATED = "state_updated_at"
ATTR_WARRANTY = "warranty"
ATTR_PARTYMODE = "party_mode_enabled"
ATTR_RSSI = "rssi"
ATTR_STATUS = "status_info"
ATTR_PROGRESS = "daily_progress"
ATTR_NEXT_SCHEDULE = "next_scheduled_start"

# Misc. attributes
ATTR_NEXT_ZONE = "next_zone"
ATTR_CLOUD = "cloud"
ATTR_DEVICES = "devices"
ATTR_DEVICEIDS = "device_ids"
ATTR_DEVICE = "device"
ATTR_API = "api"
ATTR_FEATUREBITS = "feature_bits"

# Available cloud vendors
CLOUDS = []
for name, cloud in inspect.getmembers(CloudType):
    if inspect.isclass(cloud) and not "__" in name:
        CLOUDS.append(name.capitalize())

# State mapping
STATE_MAP = {
    0: STATE_IDLE,
    1: LawnMowerActivity.DOCKED,
    2: STATE_STARTING,
    3: STATE_STARTING,
    4: STATE_RETURNING,
    5: STATE_RETURNING,
    6: STATE_RETURNING,
    7: LawnMowerActivity.MOWING,
    8: LawnMowerActivity.ERROR,
    9: LawnMowerActivity.ERROR,
    10: LawnMowerActivity.ERROR,
    11: LawnMowerActivity.ERROR,
    12: LawnMowerActivity.MOWING,
    13: STATE_ESCAPED_DIGITAL_FENCE,
    30: STATE_RETURNING,
    31: STATE_ZONING,
    32: STATE_EDGECUT,
    33: STATE_STARTING,
    34: LawnMowerActivity.PAUSED,
    103: STATE_SEARCHING_ZONE,
    104: STATE_RETURNING,
}

# Error mapping
ERROR_MAP = {
    -1: STATE_UNKNOWN,
    0: STATE_NO_ERROR,
    1: STATE_TRAPPED,
    2: STATE_LIFTED,
    3: STATE_WIRE_MISSING,
    4: STATE_OUTSIDE_WIRE,
    5: STATE_RAINDELAY,
    6: STATE_CLOSE_DOOR_MOW,
    7: STATE_CLOSE_DOOR_HOME,
    8: STATE_BLADE_BLOCKED,
    9: STATE_WHEEL_BLOCKED,
    10: STATE_TRAPPED_TIMEOUT,
    11: STATE_UPSIDE_DOWN,
    12: STATE_BATTERY_LOW,
    13: STATE_REVERSE_WIRE,
    14: STATE_CHARGING_ERROR,
    15: STATE_TIMEOUT_HOME,
    16: STATE_LOCKED,
    17: STATE_BATTERY_TEMPERATURE_ERROR,
    19: STATE_BATTERY_OPEN,
    20: STATE_WIRE_SYNC,
    100: STATE_DOCKING_ERROR,
    101: STATE_HBI_ERROR,
    102: STATE_OTA_ERROR,
    103: STATE_MAP_ERROR,
    104: STATE_EXESSIVE_SLOPE,
    105: STATE_UNREACHABLE_ZONE,
    106: STATE_UNREACHABLE_DOCK,
    108: STATE_INSUFFICIENT_SENSOR_DATA,
    109: STATE_TRAINING_START_DISALLOWED,
    110: STATE_CAMERA_ERROR,
    111: STATE_MAPPING_REQUIRED,
    112: STATE_MAPPING_FAILED,
    113: STATE_RFID_ERROR,
    114: STATE_HEADLIGHT_ERROR,
    115: STATE_MISSING_DOCK,
    116: STATE_HEIGHT_BLOCKED,
}

# Remap the zones to be more "human-readable"
ZONE_MAP = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
}


class LandroidButtonTypes(StrEnum):
    """Defines different button types for Landroid Cloud integration."""

    RESTART = SERVICE_RESTART
    EDGECUT = SERVICE_EDGECUT


class LandroidSelectTypes(StrEnum):
    """Defines different button types for Landroid Cloud integration."""

    NEXT_ZONE = ATTR_NEXT_ZONE


@dataclass
class ScheduleDays(IntEnum):
    """Schedule types."""

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


# Map schedule to Landroid JSON property
SCHEDULE_TYPE_MAP = {
    "primary": "d",
    "secondary": "dd",
}

# Map button type to service
BUTTONTYPE_TO_SERVICE = {
    LandroidButtonTypes.RESTART: SERVICE_RESTART,
    LandroidButtonTypes.EDGECUT: SERVICE_EDGECUT,
}

# Map schedule days
SCHEDULE_TO_DAY = {
    "sunday": {
        "day": ScheduleDays.SUNDAY,
        "start": ATTR_SUNDAY_START,
        "end": ATTR_SUNDAY_END,
        "boundary": ATTR_SUNDAY_BOUNDARY,
        "clear": "sunday",
    },
    "monday": {
        "day": ScheduleDays.MONDAY,
        "start": ATTR_MONDAY_START,
        "end": ATTR_MONDAY_END,
        "boundary": ATTR_MONDAY_BOUNDARY,
        "clear": "monday",
    },
    "tuesday": {
        "day": ScheduleDays.TUESDAY,
        "start": ATTR_TUESDAY_START,
        "end": ATTR_TUESDAY_END,
        "boundary": ATTR_TUESDAY_BOUNDARY,
        "clear": "tuesday",
    },
    "wednesday": {
        "day": ScheduleDays.WEDNESDAY,
        "start": ATTR_WEDNESDAY_START,
        "end": ATTR_WEDNESDAY_END,
        "boundary": ATTR_WEDNESDAY_BOUNDARY,
        "clear": "wednesday",
    },
    "thursday": {
        "day": ScheduleDays.THURSDAY,
        "start": ATTR_THURSDAY_START,
        "end": ATTR_THURSDAY_END,
        "boundary": ATTR_THURSDAY_BOUNDARY,
        "clear": "thursday",
    },
    "friday": {
        "day": ScheduleDays.FRIDAY,
        "start": ATTR_FRIDAY_START,
        "end": ATTR_FRIDAY_END,
        "boundary": ATTR_FRIDAY_BOUNDARY,
        "clear": "friday",
    },
    "saturday": {
        "day": ScheduleDays.SATURDAY,
        "start": ATTR_SATURDAY_START,
        "end": ATTR_SATURDAY_END,
        "boundary": ATTR_SATURDAY_BOUNDARY,
        "clear": "saturday",
    },
}


class LandroidFeatureSupport(IntEnum):
    """Supported features of the Landroid integration."""

    MOWER = 1
    BUTTON = 2
    SELECT = 4
    SETZONE = 8
    RESTART = 16
    LOCK = 32
    OTS = 64
    EDGECUT = 128
    PARTYMODE = 256
    CONFIG = 512
    SCHEDULES = 1024
    TORQUE = 2048
    RAW = 4096


API_TO_INTEGRATION_FEATURE_MAP = {
    DeviceCapability.EDGE_CUT: LandroidFeatureSupport.EDGECUT,
    DeviceCapability.ONE_TIME_SCHEDULE: LandroidFeatureSupport.OTS,
    DeviceCapability.PARTY_MODE: LandroidFeatureSupport.PARTYMODE,
    DeviceCapability.TORQUE: LandroidFeatureSupport.TORQUE,
}
