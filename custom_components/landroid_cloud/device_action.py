"""Provides device automations for Vacuum."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.device_automation import async_validate_entity_schema
from homeassistant.components.lawn_mower.const import (
    SERVICE_DOCK,
    SERVICE_PAUSE,
    SERVICE_START_MOWING,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

MOWER_DOMAIN = "lawn_mower"

ACTION_TYPES = {"mow", "dock", "pause"}

_ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
    }
)


async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    return async_validate_entity_schema(hass, config, _ACTION_SCHEMA)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Vacuum devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != MOWER_DOMAIN:
            continue

        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        actions += [{**base_action, CONF_TYPE: action} for action in ACTION_TYPES]

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == "mow":
        service = SERVICE_START_MOWING
        service_domain = MOWER_DOMAIN
    elif config[CONF_TYPE] == "dock":
        service = SERVICE_DOCK
        service_domain = MOWER_DOMAIN
    elif config[CONF_TYPE] == "pause":
        service = SERVICE_PAUSE
        service_domain = MOWER_DOMAIN

    await hass.services.async_call(
        service_domain, service, service_data, blocking=True, context=context
    )
