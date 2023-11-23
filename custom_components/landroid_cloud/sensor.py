"""Sensors for landroid_cloud."""
from __future__ import annotations

from datetime import datetime, timezone

import pytz
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_utils

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidSensor, LandroidSensorEntityDescription

SENSORS = [
    LandroidSensorEntityDescription(
        key="battery_state",
        name="Battery",
        entity_category=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        entity_registry_enabled_default=True,
        native_unit_of_measurement="%",
        value_fn=lambda landroid: landroid.battery["percent"]
        if "percent" in landroid.battery
        else None,
        attributes=["charging"],
    ),
    LandroidSensorEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="°C",
        value_fn=lambda landroid: landroid.battery["temperature"]
        if "temperature" in landroid.battery
        else None,
    ),
    LandroidSensorEntityDescription(
        key="battery_cycles_total",
        name="Battery Total Charge Cycles",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=" ",
        value_fn=lambda landroid: landroid.battery["cycles"]["total"]
        if "cycles" in landroid.battery
        else None,
        icon="mdi:battery-sync",
    ),
    LandroidSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="V",
        value_fn=lambda landroid: landroid.battery["voltage"]
        if "voltage" in landroid.battery
        else None,
    ),
    LandroidSensorEntityDescription(
        key="blades_total_on",
        name="Blades Total On Time",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="hours",
        suggested_display_precision=0,
        value_fn=lambda landroid: round(landroid.blades["total_on"] / 60, 0)
        if "total_on" in landroid.blades
        else None,
        icon="mdi:saw-blade",
    ),
    LandroidSensorEntityDescription(
        key="blades_current_on",
        name="Blades Current On Time",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="hours",
        suggested_display_precision=0,
        value_fn=lambda landroid: round(landroid.blades["current_on"] / 60, 0)
        if "current_on" in landroid.blades
        else None,
        icon="mdi:saw-blade",
    ),
    LandroidSensorEntityDescription(
        key="blades_reset_at",
        name="Blades Reset At Hours",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="hours",
        suggested_display_precision=0,
        value_fn=lambda landroid: round(landroid.blades["reset_at"] / 60, 0)
        if "reset_at" in landroid.blades
        else None,
        icon="mdi:history",
    ),
    LandroidSensorEntityDescription(
        key="blades_reset_time",
        name="Blades Reset At",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="",
        value_fn=lambda landroid: landroid.blades["reset_time"]
        if "reset_time" in landroid.blades
        else None,
    ),
    LandroidSensorEntityDescription(
        key="error",
        name="Error",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=None,
        device_class=SensorDeviceClass.ENUM,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=None,
        value_fn=lambda landroid: landroid.error["description"],
        attributes=["id"],
        icon="mdi:alert-circle",
    ),
    LandroidSensorEntityDescription(
        key="pitch",
        name="Pitch",
        entity_category=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="°",
        value_fn=lambda landroid: landroid.orientation["pitch"],
        suggested_display_precision=1,
        icon="mdi:axis-x-rotate-clockwise",
    ),
    LandroidSensorEntityDescription(
        key="roll",
        name="Roll",
        entity_category=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="°",
        value_fn=lambda landroid: landroid.orientation["roll"],
        suggested_display_precision=1,
        icon="mdi:axis-y-rotate-clockwise",
    ),
    LandroidSensorEntityDescription(
        key="yaw",
        name="Yaw",
        entity_category=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="°",
        value_fn=lambda landroid: landroid.orientation["yaw"],
        suggested_display_precision=1,
        icon="mdi:axis-z-rotate-clockwise",
    ),
    LandroidSensorEntityDescription(
        key="rainsensor_delay",
        name="Rainsensor Delay",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement="minutes",
        value_fn=lambda landroid: landroid.rainsensor["delay"]
        if "delay" in landroid.rainsensor
        else None,
        icon="mdi:weather-rainy",
    ),
    LandroidSensorEntityDescription(
        key="rainsensor_remaining",
        name="Rainsensor Remaining",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="minutes",
        value_fn=lambda landroid: landroid.rainsensor["remaining"]
        if "remaining" in landroid.rainsensor
        else None,
        icon="mdi:weather-rainy",
    ),
    LandroidSensorEntityDescription(
        key="distance",
        name="Distance Driven",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DISTANCE,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="km",
        suggested_display_precision=0,
        value_fn=lambda landroid: round(landroid.statistics["distance"] / 1000, 0)
        if "distance" in landroid.statistics
        else None,
    ),
    LandroidSensorEntityDescription(
        key="worktime_total",
        name="Total Worktime",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="hours",
        suggested_display_precision=0,
        value_fn=lambda landroid: round(landroid.statistics["worktime_total"] / 60, 0)
        if "worktime_total" in landroid.statistics
        else None,
        icon="mdi:update",
    ),
    LandroidSensorEntityDescription(
        key="rssi",
        name="Rssi",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_registry_enabled_default=True,
        native_unit_of_measurement="dBm",
        value_fn=lambda landroid: landroid.rssi,
    ),
    LandroidSensorEntityDescription(
        key="last_update",
        name="Last Update",
        entity_category=None,
        state_class=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=None,
        value_fn=lambda landroid: landroid.last_status["timestamp"].astimezone(
            pytz.utc
        ),
        icon="mdi:clock-check",
    ),
    LandroidSensorEntityDescription(
        key="next_start",
        name="Next Scheduled Start",
        entity_category=None,
        state_class=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=None,
        value_fn=lambda landroid: landroid.schedules["next_schedule_start"],
        icon="mdi:clock-start",
        attributes=["schedule"],
    ),
    LandroidSensorEntityDescription(
        key="daily_progress",
        name="Daily Progress",
        entity_category=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="%",
        value_fn=lambda landroid: landroid.schedules["daily_progress"],
        icon="mdi:progress-clock",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the sensor platform."""
    sensors = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        for sens in SENSORS:
            entity = LandroidSensor(hass, sens, api, config)

            sensors.append(entity)

    async_add_devices(sensors)
