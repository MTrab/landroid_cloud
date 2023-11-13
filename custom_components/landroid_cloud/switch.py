"""Switches for landroid_cloud."""
from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN
from .device_base import LandroidSwitch, LandroidSwitchEntityDescription

SWITCHES = [
    LandroidSwitchEntityDescription(
        key="partymode",
        name="Party Mode",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=False,
        value_fn=lambda landroid: landroid.partymode_enabled,
        command_fn=lambda landroid, serial, state: landroid.set_partymode(
            serial, state
        ),
        icon="mdi:party-popper",
    ),
    LandroidSwitchEntityDescription(
        key="locked",
        name="Locked",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=False,
        value_fn=lambda landroid: landroid.locked,
        command_fn=lambda landroid, serial, state: landroid.set_lock(serial, state),
        icon_on="mdi:lock",
        icon_off="mdi:lock-open",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_devices,
) -> None:
    """Set up the switch platform."""
    switches = []
    for _, info in hass.data[DOMAIN][config.entry_id][ATTR_DEVICES].items():
        api: LandroidAPI = info["api"]
        for sens in SWITCHES:
            entity = LandroidSwitch(hass, sens, api, config)

            switches.append(entity)

    async_add_devices(switches)
