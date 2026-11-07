"""Number platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfArea, UnitOfLength
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


def _time_extension_value(device) -> int | None:
    """Return schedule time extension percentage when available."""
    value = getattr(device, "schedules", {}).get("time_extension")
    return None if value is None else int(value)


def _torque_value(device) -> int | None:
    """Return torque as an integer percentage when available."""
    value = getattr(device, "torque", None)
    return None if value is None else int(value)


def _lawn_value(device, key: str) -> int | None:
    """Return one lawn parameter as an integer when available."""
    value = getattr(device, "lawn", {}).get(key)
    return None if value is None else int(value)


NUMBERS: tuple[LandroidNumberDescription, ...] = (
    LandroidNumberDescription(
        key="rain_delay",
        translation_key="rain_delay",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=0,
        native_max_value=1440,
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
        native_step=5,
        native_unit_of_measurement="mm",
        mode=NumberMode.SLIDER,
        capability=DeviceCapability.CUTTING_HEIGHT,
    ),
    LandroidNumberDescription(
        key="time_extension",
        translation_key="time_extension",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=-100,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        mode=NumberMode.BOX,
        icon="mdi:timer-edit-outline",
    ),
    LandroidNumberDescription(
        key="torque",
        translation_key="torque",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=-50,
        native_max_value=50,
        native_step=1,
        native_unit_of_measurement="%",
        mode=NumberMode.SLIDER,
        icon="mdi:gauge",
        capability=DeviceCapability.TORQUE,
    ),
    LandroidNumberDescription(
        key="lawn_size",
        translation_key="lawn_size",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=0,
        native_max_value=100000,
        native_step=1,
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        mode=NumberMode.BOX,
        icon="mdi:texture-box",
    ),
    LandroidNumberDescription(
        key="lawn_perimeter",
        translation_key="lawn_perimeter",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        native_min_value=0,
        native_max_value=100000,
        native_step=1,
        native_unit_of_measurement=UnitOfLength.METERS,
        mode=NumberMode.BOX,
        icon="mdi:ruler-square",
    ),
)

ZONE_CUTTING_HEIGHT_DESCRIPTION = LandroidNumberDescription(
    key="zone_cutting_height",
    translation_key="zone_cutting_height",
    entity_category=EntityCategory.CONFIG,
    entity_registry_enabled_default=False,
    native_min_value=20,
    native_max_value=70,
    native_step=5,
    native_unit_of_measurement="mm",
    mode=NumberMode.SLIDER,
    capability=DeviceCapability.CUTTING_HEIGHT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud number entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidNumber | LandroidZoneCuttingHeightNumber] = []

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

        if device.capabilities.check(DeviceCapability.CUTTING_HEIGHT):
            try:
                zone_heights = coordinator.cloud.get_zone_cutting_heights(serial_number)
            except NoCuttingHeightError:
                zone_heights = {}
            entities.extend(
                LandroidZoneCuttingHeightNumber(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    zone_id=zone_id,
                )
                for zone_id in zone_heights
            )

    async_add_entities(entities)


class LandroidNumber(LandroidBaseEntity, NumberEntity):
    """Representation of a Landroid cloud number entity."""

    entity_description: LandroidNumberDescription
    _attr_requires_online = True

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

        if self.entity_description.key == "time_extension":
            return _time_extension_value(self.device)

        if self.entity_description.key == "torque":
            return _torque_value(self.device)

        if self.entity_description.key == "lawn_size":
            return _lawn_value(self.device, "size")

        if self.entity_description.key == "lawn_perimeter":
            return _lawn_value(self.device, "perimeter")

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
        elif self.entity_description.key == "time_extension":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_time_extension(
                    serial_number, int(value)
                )
            )
        elif self.entity_description.key == "torque":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_torque(serial_number, int(value))
            )
        elif self.entity_description.key == "lawn_size":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_lawn_size(serial_number, int(value))
            )
        elif self.entity_description.key == "lawn_perimeter":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_lawn_perimeter(
                    serial_number, int(value)
                )
            )


class LandroidZoneCuttingHeightNumber(LandroidBaseEntity, NumberEntity):
    """Configured cutting height for one RTK zone."""

    entity_description = ZONE_CUTTING_HEIGHT_DESCRIPTION
    _attr_requires_online = True

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        zone_id: int,
    ) -> None:
        """Initialize an RTK zone cutting-height entity."""
        self._zone_id = zone_id
        self._attr_translation_placeholders = {"zone": str(zone_id)}
        super().__init__(
            coordinator,
            config_entry,
            serial_number,
            f"zone_{zone_id}_cutting_height",
        )

    @property
    def native_value(self) -> float | None:
        """Return the zone's configured cutting height."""
        try:
            heights = self.coordinator.cloud.get_zone_cutting_heights(
                str(self.device.serial_number)
            )
        except NoCuttingHeightError:
            return None
        height = heights.get(self._zone_id)
        return float(height) if height is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set the zone's configured cutting height."""
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.set_zone_cutting_height(
                str(self.device.serial_number),
                self._zone_id,
                int(value),
            )
        )
