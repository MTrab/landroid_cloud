"""Switch platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyworxcloud import DeviceCapability

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity


@dataclass(frozen=True, kw_only=True)
class LandroidSwitchDescription(SwitchEntityDescription):
    """Description for Landroid switches."""

    capability: DeviceCapability | None = None


SWITCHES: tuple[LandroidSwitchDescription, ...] = (
    LandroidSwitchDescription(
        key="party_mode",
        translation_key="party_mode",
        icon="mdi:party-popper",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        capability=DeviceCapability.PARTY_MODE,
    ),
    LandroidSwitchDescription(
        key="lock",
        translation_key="lock",
        icon="mdi:lock",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    LandroidSwitchDescription(
        key="off_limits",
        translation_key="off_limits",
        icon="mdi:border-none-variant",
        entity_category=EntityCategory.CONFIG,
        capability=DeviceCapability.OFF_LIMITS,
    ),
    LandroidSwitchDescription(
        key="off_limits_shortcut",
        translation_key="off_limits_shortcut",
        icon="mdi:transit-detour",
        entity_category=EntityCategory.CONFIG,
        capability=DeviceCapability.OFF_LIMITS,
    ),
    LandroidSwitchDescription(
        key="acs",
        translation_key="acs",
        icon="mdi:radar",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        capability=DeviceCapability.ACS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud switch entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidSwitch] = []

    for serial_number, device in coordinator.data.items():
        for description in SWITCHES:
            if description.capability and not device.capabilities.check(
                description.capability
            ):
                continue

            entities.append(
                LandroidSwitch(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidSwitch(LandroidBaseEntity, SwitchEntity):
    """Representation of a Landroid cloud switch."""

    entity_description: LandroidSwitchDescription
    _attr_requires_online = True

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidSwitchDescription,
    ) -> None:
        """Initialize switch entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        key = self.entity_description.key
        if key == "party_mode":
            return bool(self.device.schedules.get("party_mode_enabled", False))
        if key == "lock":
            locked = getattr(self.device, "locked", None)
            return None if locked is None else bool(locked)
        if key == "off_limits":
            value = getattr(self.device, "offlimit", None)
            return None if value is None else bool(value)
        if key == "off_limits_shortcut":
            value = getattr(self.device, "offlimit_shortcut", None)
            return None if value is None else bool(value)
        if key == "acs":
            value = getattr(self.device, "acs_enabled", None)
            return None if value is None else bool(value)

        return None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off switch."""
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Apply the selected switch state in the cloud API."""
        serial_number = str(self.device.serial_number)

        if self.entity_description.key == "party_mode":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_partymode(serial_number, state)
            )
        elif self.entity_description.key == "lock":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_lock(serial_number, state)
            )
        elif self.entity_description.key == "off_limits":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_offlimits(serial_number, state)
            )
        elif self.entity_description.key == "off_limits_shortcut":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_offlimits_shortcut(
                    serial_number, state
                )
            )
        elif self.entity_description.key == "acs":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_acs(serial_number, state)
            )
