"""Constants for the Landroid Cloud integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "landroid_cloud"

PLATFORMS: list[Platform] = [
    Platform.LAWN_MOWER,
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
