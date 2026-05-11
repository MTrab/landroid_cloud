"""Constants for the Landroid Cloud integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform
from pyworxcloud.day_map import DAY_MAP

DOMAIN = "landroid_cloud"

PLATFORMS: list[Platform] = [
    Platform.LAWN_MOWER,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.UPDATE,
]

STARTUP = """
-------------------------------------------------------------------
Landroid Cloud integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/landroid_cloud/issues
-------------------------------------------------------------------
"""

CONF_CLOUD = "cloud"
CONF_COMMAND_TIMEOUT = "command_timeout"

DEFAULT_CLOUD = "worx"
DEFAULT_COMMAND_TIMEOUT = 30.0
MIN_COMMAND_TIMEOUT = 1.0
MAX_COMMAND_TIMEOUT = 120.0

MOWER_STATE_IDLE = "idle"
MOWER_STATE_STARTING = "starting"
MOWER_STATE_EDGECUT = "edgecut"
MOWER_STATE_ZONING = "zoning"
MOWER_STATE_SEARCHING_ZONE = "searching_zone"
MOWER_STATE_ESCAPED_DIGITAL_FENCE = "escaped_digital_fence"
MOWER_STATE_RAIN_DELAY = "rain_delayed"


class CloudProvider(StrEnum):
    """Supported cloud providers."""

    WORX = "worx"
    KRESS = "kress"
    LANDXCAPE = "landxcape"


ERROR_STATE_MAP: dict[int, str] = {
    -1: "unknown",
    0: "no_error",
    1: "trapped",
    2: "lifted",
    3: "wire_missing",
    4: "outside_wire",
    5: "rain_delay",
    6: "close_door_to_mow",
    7: "close_door_to_go_home",
    8: "blade_motor_blocked",
    9: "wheel_motor_blocked",
    10: "trapped_timeout",
    11: "upside_down",
    12: "battery_low",
    13: "reverse_wire",
    14: "charge_error",
    15: "timeout_finding_home",
    16: "locked",
    17: "battery_temperature_error",
    19: "battery_trunk_open_timeout",
    20: "wire_sync",
    100: "charging_station_docking_error",
    101: "hbi_error",
    102: "ota_error",
    103: "map_error",
    104: "excessive_slope",
    105: "unreachable_zone",
    106: "unreachable_charging_station",
    108: "insufficient_sensor_data",
    109: "training_start_disallowed",
    110: "camera_error",
    111: "mapping_exploration_required",
    112: "mapping_exploration_failed",
    113: "rfid_reader_error",
    114: "headlight_error",
    115: "missing_charging_station",
    116: "blade_height_adjustment_blocked",
}
ERROR_STATE_OPTIONS: tuple[str, ...] = tuple(dict.fromkeys(ERROR_STATE_MAP.values()))

SERVICE_OTS = "ots"
SERVICE_SET_BORDER_CUT_SETTINGS = "set_border_cut_settings"
SERVICE_ADD_SCHEDULE = "add_schedule"
SERVICE_EDIT_SCHEDULE = "edit_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_SET_NUTRITION = "set_nutrition"
SERVICE_CLEAR_NUTRITION = "clear_nutrition"
SERVICE_SET_EXCLUSION_DAY = "set_exclusion_day"
SERVICE_ADD_EXCLUSION_SCHEDULE = "add_exclusion_schedule"
SERVICE_EDIT_EXCLUSION_SCHEDULE = "edit_exclusion_schedule"
SERVICE_DELETE_EXCLUSION_SCHEDULE = "delete_exclusion_schedule"

ATTR_EXCLUDE_DAY = "exclude_day"
ATTR_K = "k"
ATTR_N = "n"
ATTR_P = "p"
ATTR_REASON = "reason"
ATTR_BOUNDARY = "boundary"
ATTR_ALL_SCHEDULES = "all_schedules"
ATTR_CURRENT_DAY = "current_day"
ATTR_CURRENT_START = "current_start"
ATTR_DAY = "day"
ATTR_DAYS = "days"
ATTR_DURATION = "duration"
ATTR_RUNTIME = "runtime"
ATTR_CUT_OVER_BORDER = "cut_over_border"
ATTR_BORDER_DISTANCE_CM = "border_distance_cm"
ATTR_START = "start"

DAYS = tuple(DAY_MAP[index] for index in sorted(DAY_MAP))
EXCLUSION_REASONS = ("generic", "irrigation")
VISION_BORDER_DISTANCE_CM_VALUES = (5, 10, 15, 20)

AUTO_SCHEDULE_BOOST_OPTIONS = ("0", "1", "2")
AUTO_SCHEDULE_GRASS_TYPE_OPTIONS = (
    "mixed_species",
    "festuca_arundinacea",
    "lolium_perenne",
    "poa_pratensis",
    "festuca_rubra",
    "agrostis_stolonifera",
)
AUTO_SCHEDULE_SOIL_TYPE_OPTIONS = ("clay", "silt", "sand", "ignore")
