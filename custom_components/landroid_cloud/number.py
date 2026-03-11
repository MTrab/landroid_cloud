"""Number platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyworxcloud import DeviceCapability
from pyworxcloud.exceptions import NoCuttingHeightError

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity


@dataclass(frozen=True, kw_only=True)
class LandroidNumberDescription(NumberEntityDescription):
    """Description for Landroid numbers."""

    capability: DeviceCapability | None = None


def _rain_delay_value(device) -> int | None:
    """Return rain delay as an integer when available."""
    value = getattr(device, "rainsensor", {}).get("delay")
    return None if value is None else int(value)


NUMBERS: tuple[LandroidNumberDescription, ...] = (
    LandroidNumberDescription(
        key="rain_delay",
        translation_key="rain_delay",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=0,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement="min",
        mode=NumberMode.BOX,
        icon="mdi:weather-rainy",
    ),
    LandroidNumberDescription(
        key="cutting_height",
        translation_key="cutting_height",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=20,
        native_max_value=70,
        native_step=1,
        native_unit_of_measurement="mm",
        mode=NumberMode.SLIDER,
        capability=DeviceCapability.CUTTING_HEIGHT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud number entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidNumber] = []

    for serial_number, device in coordinator.data.items():
        for description in NUMBERS:
            if description.capability and not device.capabilities.check(
                description.capability
            ):
                continue

            entities.append(
                LandroidNumber(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidNumber(LandroidBaseEntity, NumberEntity):
    """Representation of a Landroid cloud number entity."""

    entity_description: LandroidNumberDescription

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidNumberDescription,
    ) -> None:
        """Initialize number entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def native_value(self) -> float | None:
        """Return number value."""
        serial_number = str(self.device.serial_number)

        if self.entity_description.key == "rain_delay":
            return _rain_delay_value(self.device)

        if self.entity_description.key == "cutting_height":
            try:
                return float(self.coordinator.cloud.get_cutting_height(serial_number))
            except NoCuttingHeightError:
                return None

        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new number value."""
        serial_number = str(self.device.serial_number)

        if self.entity_description.key == "rain_delay":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.raindelay(serial_number, str(int(value)))
            )
        elif self.entity_description.key == "cutting_height":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_cutting_height(
                    serial_number, int(value)
                )
            )
