"""Provide the device automations for Vacuum."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.lawn_mower.const import LawnMowerActivity
from homeassistant.const import (
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import condition
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from custom_components.landroid_cloud.const import STATE_EDGECUT

from . import DOMAIN

MOWER_DOMAIN = "lawn_mower"

CONDITION_TYPES = {"is_mowing", "is_docked", "is_edgecut", "has_error", "is_returning"}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for Landroid Cloud devices."""
    registry = er.async_get(hass)
    conditions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != MOWER_DOMAIN:
            continue

        base_condition = {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        conditions += [{**base_condition, CONF_TYPE: cond} for cond in CONDITION_TYPES]

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config[CONF_TYPE] == "is_docked":
        test_states = [LawnMowerActivity.DOCKED]
    elif config[CONF_TYPE] == "is_mowing":
        test_states = [LawnMowerActivity.MOWING]
    elif config[CONF_TYPE] == "is_edgecut":
        test_states = [STATE_EDGECUT]
    elif config[CONF_TYPE] == "has_error":
        test_states = [LawnMowerActivity.ERROR]
    elif config[CONF_TYPE] == "is_returning":
        test_states = [LawnMowerActivity.RETURNING]

    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return (
            entity_id is not None
            and (state := hass.states.get(entity_id)) is not None
            and state.state in test_states
        )

    return test_is_state
