"""Switches for landroid_cloud."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api import LandroidAPI
from .const import ATTR_DEVICES, DOMAIN, LOGLEVEL, LandroidFeatureSupport
from .device_base import LandroidSwitch, LandroidSwitchEntityDescription
from .utils.logger import LandroidLogger, LoggerType

SWITCHES = [
    LandroidSwitchEntityDescription(
        key="partymode",
        name="Party Mode",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=True,
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
    LandroidSwitchEntityDescription(
        key="offlimits",
        name="Off limits",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.offlimit,
        command_fn=lambda landroid, serial, state: landroid.set_offlimits(
            serial, state
        ),
        icon="mdi:border-none-variant",
        required_feature=LandroidFeatureSupport.OFFLIMITS,
    ),
    LandroidSwitchEntityDescription(
        key="offlimits_shortcut",
        name="Shortcuts",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.offlimit_shortcut,
        command_fn=lambda landroid, serial, state: landroid.set_offlimits_shortcut(
            serial, state
        ),
        icon="mdi:transit-detour",
        required_feature=LandroidFeatureSupport.OFFLIMITS,
    ),
    LandroidSwitchEntityDescription(
        key="acs",
        name="ACS",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=True,
        value_fn=lambda landroid: landroid.acs_enabled,
        command_fn=lambda landroid, serial, state: landroid.set_acs(
            serial, state
        ),
        icon="mdi:transit-connection-variant",
        required_feature=LandroidFeatureSupport.ACS,
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
        logger = LandroidLogger(name=__name__, api=api, log_level=LOGLEVEL)
        for sens in SWITCHES:
            logger.log(
                LoggerType.API,
                "API features: %s, Required feature: %s",
                api.features,
                sens.required_feature,
            )
            if isinstance(sens.required_feature, type(None)) or (
                api.features & sens.required_feature
            ):
                entity = LandroidSwitch(hass, sens, api, config)

                switches.append(entity)

    async_add_devices(switches)
