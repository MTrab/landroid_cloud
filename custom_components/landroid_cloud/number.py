"""Input numbers for landroid_cloud."""

from __future__ import annotations

import json
import logging

from homeassistant.components.number import NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyworxcloud import DeviceCapability

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidNumber, LandroidNumberEntityDescription

INPUT_NUMBERS = [
    # LandroidNumberEntityDescription(
    #     key="timeextention",
    #     name="Time extention",
    #     entity_category=EntityCategory.CONFIG,
    #     device_class=None,
    #     entity_registry_enabled_default=True,
    #     native_unit_of_measurement="%",
    #     max_value=100,
    #     min_value=-100,
    #     value_fn=lambda api: api.de,
    #     command_fn=None,
    #     required_protocol=0,
    # ),
    LandroidNumberEntityDescription(
        key="torque",
        name="Torque",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=None,
        max_value=50,
        min_value=-50,
        native_step=1,
        value_fn=lambda api: api.device.torque,
        command_fn=lambda api, value: api.cloud.send(api.device.serial_number, json.dumps({"tq": value})),
        required_capability=DeviceCapability.TORQUE
    ),
]

_LOGGER = logging.getLogger(__name__)

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
            if (isinstance(number.required_protocol, type(None)) or number.required_protocol == api.device.protocol):
                if (api.device.capabilities.check(number.required_capability)):
                    _LOGGER.debug("Added number for %s", number.key)
                    entity = LandroidNumber(hass, number, api, config)
                    entities.append(entity)

    async_add_devices(entities)