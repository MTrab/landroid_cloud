"""Support for Landroid cloud compatible mowers."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LandroidAPI
from .const import (
    DOMAIN,
    LOGLEVEL,
)

from .utils.entity_setup import vendor_to_device
from .utils.logger import LandroidLogger, LoggerType


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the mower device."""
    mowers = []
    for idx in range(hass.data[DOMAIN][config.entry_id]["count"]):
        api: LandroidAPI = hass.data[DOMAIN][config.entry_id][idx]["api"]
        device = vendor_to_device(api.config["type"])
        constructor = device.MowerDevice(hass, api)

        logger = LandroidLogger(name=__name__, api=api, log_level=LOGLEVEL)
        if not api.features_loaded:
            logger.log(LoggerType.SETUP, "Features not assessed, calling assessment")
            api.check_features(
                int(constructor.base_features), constructor.register_services
            )

        mowers.append(constructor)

    async_add_entities(mowers, True)
