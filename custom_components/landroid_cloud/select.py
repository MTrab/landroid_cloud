"""Select platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity, auto_schedule_settings

AUTO_SCHEDULE_BOOST_OPTIONS: Final = ("0", "1", "2")
AUTO_SCHEDULE_GRASS_TYPE_OPTIONS: Final = (
    "mixed_species",
    "festuca_arundinacea",
    "lolium_perenne",
    "poa_pratensis",
    "festuca_rubra",
    "agrostis_stolonifera",
)
AUTO_SCHEDULE_SOIL_TYPE_OPTIONS: Final = ("clay", "silt", "sand", "ignore")


def _configured_legacy_zone_options(device) -> list[str]:
    """Return configured legacy zone numbers when start points are known."""
    starting_points = device.zone.get("starting_point", [])
    return [
        str(index + 1)
        for index, start in enumerate(starting_points)
        if isinstance(start, int) and start > 0
    ]


def _zone_options(device) -> list[str]:
    """Return available zone options for legacy and RTK devices."""
    zone_ids = device.zone.get("ids", [])
    if zone_ids:
        return [str(zone_id) for zone_id in zone_ids]

    configured_zones = _configured_legacy_zone_options(device)
    if configured_zones:
        return configured_zones

    starting_points = device.zone.get("starting_point", [])
    zone_count = len(starting_points)
    if zone_count == 0:
        zone_count = 4
    return [str(zone) for zone in range(1, zone_count + 1)]


def _current_zone_option(device) -> str | None:
    """Return current selected zone for legacy and RTK devices."""
    zone_ids = device.zone.get("ids", [])
    if zone_ids:
        current = device.zone.get("current")
        if current in zone_ids:
            return str(int(current))
        return None

    options = _zone_options(device)
    current = device.zone.get("current")
    if isinstance(current, int):
        current_option = str(current)
        if current_option in options:
            return current_option

        current_option = str(current + 1)
        if current_option in options:
            return current_option

    index = device.zone.get("index", 0)
    current_option = str(int(index) + 1)
    if current_option in options:
        return current_option

    return None


def _auto_schedule_setting_option(device, key: str) -> str | None:
    """Return one auto-schedule setting as a string option."""
    value = auto_schedule_settings(device).get(key)
    if value is None:
        return None
    return str(value)


@dataclass(frozen=True, kw_only=True)
class LandroidSelectDescription(SelectEntityDescription):
    """Description for Landroid selects."""

    options: tuple[str, ...]


SELECTS: Final[tuple[LandroidSelectDescription, ...]] = (
    LandroidSelectDescription(
        key="zone",
        translation_key="zone",
        options=(),
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        icon="mdi:map-clock",
    ),
    LandroidSelectDescription(
        key="auto_schedule_boost",
        translation_key="auto_schedule_boost",
        options=AUTO_SCHEDULE_BOOST_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        icon="mdi:speedometer",
    ),
    LandroidSelectDescription(
        key="auto_schedule_grass_type",
        translation_key="auto_schedule_grass_type",
        options=AUTO_SCHEDULE_GRASS_TYPE_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        icon="mdi:grass",
    ),
    LandroidSelectDescription(
        key="auto_schedule_soil_type",
        translation_key="auto_schedule_soil_type",
        options=AUTO_SCHEDULE_SOIL_TYPE_OPTIONS,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        icon="mdi:shovel",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud select entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SelectEntity] = []

    for serial_number in coordinator.data:
        for description in SELECTS:
            if description.key == "zone":
                entities.append(
                    LandroidZoneSelect(
                        coordinator=coordinator,
                        config_entry=entry,
                        serial_number=serial_number,
                        description=description,
                    )
                )
                continue

            entities.append(
                LandroidAutoScheduleSelect(
                    coordinator=coordinator,
                    config_entry=entry,
                    serial_number=serial_number,
                    description=description,
                )
            )

    async_add_entities(entities)


class LandroidZoneSelect(LandroidBaseEntity, SelectEntity):
    """Representation of zone selection."""

    entity_description: LandroidSelectDescription
    _attr_requires_online = True

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidSelectDescription,
    ) -> None:
        """Initialize select entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def options(self) -> list[str]:
        """Return available zone options."""
        return _zone_options(self.device)

    @property
    def current_option(self) -> str | None:
        """Return current selected zone."""
        return _current_zone_option(self.device)

    async def async_select_option(self, option: str) -> None:
        """Set selected zone."""
        if self.device.zone.get("ids", []):
            raise HomeAssistantError(
                "Zone selection for RTK devices is not supported yet"
            )
        zone = int(option)
        serial_number = str(self.device.serial_number)
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.setzone(serial_number, zone)
        )


class LandroidAutoScheduleSelect(LandroidBaseEntity, SelectEntity):
    """Representation of one auto-schedule select."""

    entity_description: LandroidSelectDescription
    _attr_requires_online = True
    _attr_requires_auto_schedule = True

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidSelectDescription,
    ) -> None:
        """Initialize auto-schedule select entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    @property
    def options(self) -> list[str]:
        """Return valid options from pyworxcloud."""
        return list(self.entity_description.options)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        key = self.entity_description.key
        if key == "auto_schedule_boost":
            return _auto_schedule_setting_option(self.device, "boost")
        if key == "auto_schedule_grass_type":
            return _auto_schedule_setting_option(self.device, "grass_type")
        if key == "auto_schedule_soil_type":
            return _auto_schedule_setting_option(self.device, "soil_type")
        return None

    async def async_select_option(self, option: str) -> None:
        """Apply the selected option."""
        serial_number = str(self.device.serial_number)

        if option not in self.entity_description.options:
            raise HomeAssistantError(f"Invalid option: {option}")

        if self.entity_description.key == "auto_schedule_boost":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_auto_schedule_boost(
                    serial_number, int(option)
                )
            )
        elif self.entity_description.key == "auto_schedule_grass_type":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_auto_schedule_grass_type(
                    serial_number, option
                )
            )
        elif self.entity_description.key == "auto_schedule_soil_type":
            await async_run_cloud_command(
                lambda: self.coordinator.cloud.set_auto_schedule_soil_type(
                    serial_number, option
                )
            )
