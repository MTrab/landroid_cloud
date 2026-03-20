"""Provides device actions for Landroid Cloud devices."""

from __future__ import annotations

from typing import Final

import voluptuous as vol
from homeassistant.components.device_automation import async_validate_entity_schema
from homeassistant.components.lawn_mower import LawnMowerEntityFeature
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
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity import get_supported_features
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

MOWER_DOMAIN: Final = "lawn_mower"
ACTION_TO_SERVICE: Final[dict[str, str]] = {
    "start_mowing": SERVICE_START_MOWING,
    "pause": SERVICE_PAUSE,
    "dock": SERVICE_DOCK,
}
ACTION_TO_FEATURE: Final[dict[str, LawnMowerEntityFeature]] = {
    "start_mowing": LawnMowerEntityFeature.START_MOWING,
    "pause": LawnMowerEntityFeature.PAUSE,
    "dock": LawnMowerEntityFeature.DOCK,
}

_ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TO_SERVICE),
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
    }
)


async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate device action config."""
    return async_validate_entity_schema(hass, config, _ACTION_SCHEMA)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List available device actions for mower entities."""
    registry = er.async_get(hass)
    actions: list[dict[str, str]] = []

    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != MOWER_DOMAIN or entry.platform != DOMAIN:
            continue

        supported_features = get_supported_features(hass, entry.entity_id)
        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        for action_type, feature in ACTION_TO_FEATURE.items():
            if supported_features & feature:
                actions.append({**base_action, CONF_TYPE: action_type})

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a configured device action."""
    del variables

    await hass.services.async_call(
        MOWER_DOMAIN,
        ACTION_TO_SERVICE[config[CONF_TYPE]],
        {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]},
        blocking=True,
        context=context,
    )
