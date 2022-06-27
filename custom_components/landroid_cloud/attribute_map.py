"""Attribute map used by Landroid Cloud integration."""
from __future__ import annotations

ATTR_MAP = {
    "default": {
        "state": {
            "id": "cloud_id",
            "product": "device",
            "blades": "blades",
            "battery": "battery",
            "work_time": "work_time",
            "distance": "distance",
            "rssi": "rssi",
            "orientation": "orientation",
            "gps": "gps_location",
            "rainsensor": "rainsensor",
            "firmware_version": "firmware_version",
            "partymode_enabled": "partymode_enabled",
            "locked": "locked",
            "online": "online",
            "accessories": "accessories",
            "zone": "zone",
            "schedule_mower_active": "schedule_enabled",
            "schedule_variation": "time_extension",
            "schedules": "schedules",
            "error": "error",
            "torque": "wheel_torque",
            "battery_charging": "charging",
            "updated": "last_update",
            "mqttdata": "mqtt",
            "_mqtt_data": "json",
        },
        "icon": "mdi:robot-mower",
    },
}
