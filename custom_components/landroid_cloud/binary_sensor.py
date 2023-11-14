"""Binary sensors for landroid_cloud."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidBinarySensor, LandroidBinarySensorEntityDescription

BINARYSENSORS = [
    LandroidBinarySensorEntityDescription(
        key="battery_charging",
        name="Battery Charging",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.battery["charging"],
    ),
    LandroidBinarySensorEntityDescription(
        key="online",
        name="Online",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.online,
    ),
    LandroidBinarySensorEntityDescription(
        key="rainsensor_triggered",
        name="Rainsensor Triggered",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOISTURE,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.rainsensor["triggered"]
        if "triggered" in landroid.rainsensor
        else None,
        icon="mdi:weather-rainy",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the binary_sensor platform."""
    binarysensors = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        for sens in BINARYSENSORS:
            entity = LandroidBinarySensor(hass, sens, api, config)

            binarysensors.append(entity)

    async_add_devices(binarysensors)
