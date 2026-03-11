"""Button platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyworxcloud import DeviceCapability

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity


@dataclass(frozen=True, kw_only=True)
class LandroidButtonDescription(ButtonEntityDescription):
    """Description for Landroid buttons."""

    capability: DeviceCapability | None = None


BUTTONS: tuple[LandroidButtonDescription, ...] = (
    LandroidButtonDescription(
        key="edge_cut",
        translation_key="edge_cut",
        icon="mdi:map-marker-path",
        capability=DeviceCapability.EDGE_CUT,
    ),
    LandroidButtonDescription(
        key="reset_blade_time",
        translation_key="reset_blade_time",
        icon="mdi:circular-saw",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    LandroidButtonDescription(
        key="reset_battery_cycles",
        translation_key="reset_battery_cycles",
        icon="mdi:battery-sync",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud button entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidButton] = []

    for serial_number, device in coordinator.data.items():
        for description in BUTTONS:
            if description.capability and not device.capabilities.check(
                description.capability
            ):
                continue

            entities.append(
                LandroidButton(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidButton(LandroidBaseEntity, ButtonEntity):
    """Representation of a Landroid cloud button."""

    entity_description: LandroidButtonDescription

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidButtonDescription,
    ) -> None:
        """Initialize button entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    async def async_press(self) -> None:
        """Handle button press."""
        serial_number = str(self.device.serial_number)

        if self.entity_description.key == "edge_cut":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.edgecut(serial_number)
            )
        elif self.entity_description.key == "reset_blade_time":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.reset_blade_counter(serial_number)
            )
        elif self.entity_description.key == "reset_battery_cycles":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.reset_charge_cycle_counter(serial_number)
            )
