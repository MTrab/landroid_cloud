"""Representation of a button."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN, LOGLEVEL, LandroidFeatureSupport
from .device_base import LandroidButton, LandroidButtonEntityDescription
from .utils.logger import LandroidLogger, LoggerType

# Tuple containing buttons to create
BUTTONS = [
    LandroidButtonEntityDescription(
        key="restart",
        name="Restart baseboard",
        icon="mdi:restart",
        entity_category=EntityCategory.CONFIG,
        device_class=ButtonDeviceClass.RESTART,
        required_feature=None,
        press_action=lambda api, serial: api.cloud.restart(serial),
    ),
    LandroidButtonEntityDescription(
        key="edgecut",
        name="Start cutting edge",
        icon="mdi:map-marker-path",
        entity_category=None,
        required_feature=LandroidFeatureSupport.EDGECUT,
        press_action=lambda api, serial: api.cloud.ots(serial, True, 0),
    ),
    LandroidButtonEntityDescription(
        key="reset_charge_cycles",
        name="Reset charge cycles",
        icon="mdi:battery-sync",
        entity_category=EntityCategory.DIAGNOSTIC,
        required_feature=None,
        press_action=lambda api, serial: api.cloud.reset_charge_cycle_counter(serial),
    ),
    LandroidButtonEntityDescription(
        key="reset_blade_time",
        name="Reset blade time",
        icon="mdi:battery-sync",
        entity_category=EntityCategory.DIAGNOSTIC,
        required_feature=None,
        press_action=lambda api, serial: api.cloud.reset_blade_counter(serial),
    ),
    LandroidButtonEntityDescription(
        key="request_update",
        name="Request update",
        icon="mdi:refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        required_feature=None,
        entity_registry_enabled_default=False,
        press_action=lambda api, serial: api.cloud.update(serial),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Landroid buttons for specific service."""
    entities = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        logger = LandroidLogger(name=__name__, api=api, log_level=LOGLEVEL)

        for button in BUTTONS:
            if isinstance(button.required_feature, type(None)) or (
                api.features & button.required_feature
            ):
                logger.log(LoggerType.FEATURE, "Adding %s button", button.key)
                entity = LandroidButton(hass, button, api, config)

                entities.append(entity)

    async_add_entities(entities, True)
