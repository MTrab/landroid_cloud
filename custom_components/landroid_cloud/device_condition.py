"""Provides device conditions for Landroid Cloud devices."""

from __future__ import annotations

from typing import Final

import voluptuous as vol
from homeassistant.components.lawn_mower import LawnMowerActivity
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
CONDITION_STATE_MAP: Final[dict[str, tuple[str, ...]]] = {
    "is_mowing": (LawnMowerActivity.MOWING,),
    "is_docked": (LawnMowerActivity.DOCKED,),
    "has_error": (LawnMowerActivity.ERROR,),
    "is_returning": (LawnMowerActivity.RETURNING,),
    "is_edgecut": (MOWER_STATE_EDGECUT,),
    "is_starting": (MOWER_STATE_STARTING,),
    "is_zoning": (MOWER_STATE_ZONING,),
    "is_searching_zone": (MOWER_STATE_SEARCHING_ZONE,),
    "is_idle": (MOWER_STATE_IDLE,),
    "is_rain_delayed": (MOWER_STATE_RAIN_DELAY,),
    "is_escaped_digital_fence": (MOWER_STATE_ESCAPED_DIGITAL_FENCE,),
}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(CONDITION_STATE_MAP),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List available device conditions for mower entities."""
    registry = er.async_get(hass)
    conditions: list[dict[str, str]] = []

    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != MOWER_DOMAIN or entry.platform != DOMAIN:
            continue

        base_condition = {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }
        conditions.extend(
            {**base_condition, CONF_TYPE: condition_type}
            for condition_type in CONDITION_STATE_MAP
        )

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    test_states = CONDITION_STATE_MAP[config[CONF_TYPE]]

    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if the mower entity matches one of the expected states."""
        del variables
        return (
            entity_id is not None
            and (state := hass.states.get(entity_id)) is not None
            and state.state in test_states
        )

    return test_is_state
