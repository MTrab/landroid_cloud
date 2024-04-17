"""Input numbers for landroid_cloud."""

from __future__ import annotations

import json

from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyworxcloud import DeviceCapability

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidNumber, LandroidNumberEntityDescription

INPUT_NUMBERS = [
    LandroidNumberEntityDescription(
        key="timeextension",
        name="Time extension",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement="%",
        native_min_value=-100,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda api: api.cloud.devices[api.device_name].schedules[
            "time_extension"
        ],
        command_fn=lambda api, value: api.cloud.send(
            api.device.serial_number, json.dumps({"sc": {"p": value}})
        ),
        required_protocol=0,
    ),
    LandroidNumberEntityDescription(
        key="torque",
        name="Torque",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=None,
        native_min_value=-50,
        native_max_value=50,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda api: api.cloud.devices[api.device_name].torque,
        command_fn=lambda api, value: api.cloud.send(
            api.device.serial_number, json.dumps({"tq": value})
        ),
        required_capability=DeviceCapability.TORQUE,
    ),
    LandroidNumberEntityDescription(
        key="raindelay",
        name="Raindelay",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement="minutes",
        native_min_value=0,
        native_max_value=300,
        native_step=1,
        mode=NumberMode.BOX,
        value_fn=lambda api: api.device.rainsensor["delay"],
        command_fn=lambda api, value: api.cloud.raindelay(
            api.device.serial_number, value
        ),
        icon="mdi:weather-rainy",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the switch platform."""
    entities = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        for number in INPUT_NUMBERS:
            if (
                isinstance(number.required_protocol, type(None))
                or number.required_protocol == api.device.protocol
            ) and (
                isinstance(number.required_capability, type(None))
                or api.device.capabilities.check(number.required_capability)
            ):
                entity = LandroidNumber(hass, number, api, config)
                entities.append(entity)

    async_add_devices(entities)
