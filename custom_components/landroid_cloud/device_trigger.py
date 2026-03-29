"""Provides device triggers for Landroid Cloud devices."""

from __future__ import annotations

from typing import Final

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger
from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_FOR,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from . import DOMAIN
from .const import (
    MOWER_STATE_EDGECUT,
    MOWER_STATE_ESCAPED_DIGITAL_FENCE,
    MOWER_STATE_IDLE,
    MOWER_STATE_RAIN_DELAY,
    MOWER_STATE_SEARCHING_ZONE,
    MOWER_STATE_STARTING,
    MOWER_STATE_ZONING,
)

MOWER_DOMAIN: Final = "lawn_mower"
TRIGGER_STATE_MAP: Final[dict[str, str]] = {
    "mowing": LawnMowerActivity.MOWING,
    "docked": LawnMowerActivity.DOCKED,
    "error": LawnMowerActivity.ERROR,
    "returning": LawnMowerActivity.RETURNING,
    "edgecut": MOWER_STATE_EDGECUT,
    "starting": MOWER_STATE_STARTING,
    "zoning": MOWER_STATE_ZONING,
    "searching_zone": MOWER_STATE_SEARCHING_ZONE,
    "idle": MOWER_STATE_IDLE,
    "rain_delayed": MOWER_STATE_RAIN_DELAY,
    "escaped_digital_fence": MOWER_STATE_ESCAPED_DIGITAL_FENCE,
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_STATE_MAP),
        vol.Optional(CONF_FOR): cv.positive_time_period_dict,
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List available device triggers for mower entities."""
    registry = er.async_get(hass)
    triggers: list[dict[str, str]] = []

    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != MOWER_DOMAIN or entry.platform != DOMAIN:
            continue

        triggers.extend(
            {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.id,
                CONF_TYPE: trigger_type,
            }
            for trigger_type in TRIGGER_STATE_MAP
        )

    return triggers


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    del hass, config
    return {
        "extra_fields": vol.Schema(
            {vol.Optional(CONF_FOR): cv.positive_time_period_dict}
        )
    }


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a state trigger for the selected mower activity."""
    state_config = {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state_trigger.CONF_TO: TRIGGER_STATE_MAP[config[CONF_TYPE]],
    }
    if CONF_FOR in config:
        state_config[CONF_FOR] = config[CONF_FOR]

    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )
