"""Setup entity platforms."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as ha_version
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entity_platforms(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    platforms: list[str],
) -> None:
    """Set up entity platforms."""

    if ha_version >= "2022.8.0.dev0":
        _LOGGER.debug("Using post 2022.8 style loading.")
        await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    else:
        _LOGGER.debug("Using pre 2022.8 style loading.")
        hass.config_entries.async_setup_platforms(config_entry, platforms)
