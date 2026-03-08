"""Lawn mower platform for Landroid Cloud."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity

STATUS_ACTIVITY_MAP: Final[dict[int, LawnMowerActivity]] = {
    0: LawnMowerActivity.DOCKED,
    1: LawnMowerActivity.DOCKED,
    2: LawnMowerActivity.MOWING,
    3: LawnMowerActivity.MOWING,
    4: LawnMowerActivity.RETURNING,
    5: LawnMowerActivity.RETURNING,
    6: LawnMowerActivity.RETURNING,
    7: LawnMowerActivity.MOWING,
    8: LawnMowerActivity.ERROR,
    9: LawnMowerActivity.ERROR,
    10: LawnMowerActivity.ERROR,
    11: LawnMowerActivity.ERROR,
    12: LawnMowerActivity.MOWING,
    30: LawnMowerActivity.RETURNING,
    31: LawnMowerActivity.MOWING,
    32: LawnMowerActivity.MOWING,
    33: LawnMowerActivity.MOWING,
    34: LawnMowerActivity.PAUSED,
    103: LawnMowerActivity.MOWING,
    104: LawnMowerActivity.RETURNING,
}


@dataclass(frozen=True, kw_only=True)
class LandroidMowerDescription:
    """Description for mower entity."""

    key: str


MOWER_DESCRIPTION = LandroidMowerDescription(key="mower")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud lawn mower entities."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        LandroidCloudMowerEntity(coordinator, entry, serial_number)
        for serial_number in coordinator.data
    )


class LandroidCloudMowerEntity(LandroidBaseEntity, LawnMowerEntity):
    """Representation of a cloud mower."""

    entity_description = MOWER_DESCRIPTION
    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.DOCK
    )

    def __init__(self, coordinator, config_entry, serial_number: str) -> None:
        """Initialize mower entity."""
        super().__init__(coordinator, config_entry, serial_number, MOWER_DESCRIPTION.key)

    @property
    def name(self) -> str | None:
        """Return entity name."""
        return None

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return current mower activity."""
        status_id = int(getattr(self.device.status, "id", -1))
        return STATUS_ACTIVITY_MAP.get(status_id, LawnMowerActivity.ERROR)

    async def async_start_mowing(self) -> None:
        """Handle start command."""
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.start(str(self.device.serial_number))
        )

    async def async_pause(self) -> None:
        """Handle pause command."""
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.pause(str(self.device.serial_number))
        )

    async def async_dock(self) -> None:
        """Handle return-to-dock command."""
        await async_run_cloud_command(
            lambda: self.coordinator.cloud.home(str(self.device.serial_number))
        )
