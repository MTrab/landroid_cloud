"""Attribute map used by Landroid Cloud integration."""
from __future__ import annotations

ATTR_MAP = {
    "default": {
        "state": {
            "id": "cloud_id",
            "blades": "blades",
            "battery": "battery",
            "work_time": "work_time",
            "distance": "distance",
            "updated": "last_update",
            "rssi": "rssi",
            "orientation": "orientation",
            "gps": "gps_location",
            "rain_delay": "rain_delay",
            "rain_sensor_triggered": "rain_sensor_triggered",
            "rain_delay_time_remaining": "rain_delay_remaining",
            "firmware": "firmware_version",
            "serial_number": "serial",
            "mac_address": "mac",
            "partymode_enabled": "partymode_enabled",
            "locked": "locked",
            "online": "online",
            "accessories": "accessories",
            "zone_current": "current_zone",
            "zone_start": "zone_start",
            "schedule_mower_active": "schedule_enabled",
            "schedule_variation": "time_extension",
            "schedules": "schedules",
            "error": "error_id",
            "torque": "wheel_torque",
            "battery_charging": "charging",
        },
        "icon": "mdi:robot-mower",
    },
}
