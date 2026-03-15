"""Lawn mower platform for Landroid Cloud."""

from __future__ import annotations

from typing import Final

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityEntityDescription,
    LawnMowerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_platform

from .commands import async_run_cloud_command
from .entity import LandroidBaseEntity
from . import services as integration_services
from .services import (
    async_handle_add_schedule,
    async_handle_delete_schedule,
    async_handle_edit_schedule,
    async_handle_ots,
    async_register_entity_services,
)

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
MOWER_DESCRIPTION: Final = LawnMowerEntityEntityDescription(key="mower")
SERVICE_OTS: Final = integration_services.SERVICE_OTS
SERVICE_ADD_SCHEDULE: Final = integration_services.SERVICE_ADD_SCHEDULE
SERVICE_EDIT_SCHEDULE: Final = integration_services.SERVICE_EDIT_SCHEDULE
SERVICE_DELETE_SCHEDULE: Final = integration_services.SERVICE_DELETE_SCHEDULE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud lawn mower entities."""
    coordinator = entry.runtime_data.coordinator
    platform = entity_platform.async_get_current_platform()
    async_register_entity_services(platform)

    async_add_entities(
        LandroidCloudMowerEntity(coordinator, entry, serial_number)
        for serial_number in coordinator.data
    )


class LandroidCloudMowerEntity(LandroidBaseEntity, LawnMowerEntity):
    """Representation of a cloud mower."""

    entity_description = MOWER_DESCRIPTION
    _attr_requires_online = True
    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.DOCK
    )

    def __init__(self, coordinator, config_entry, serial_number: str) -> None:
        """Initialize mower entity."""
        super().__init__(
            coordinator, config_entry, serial_number, MOWER_DESCRIPTION.key
        )

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

    async def _async_service_ots(self, boundary: bool, runtime: int) -> None:
        """Handle legacy OTS service call."""
        await async_handle_ots(self, boundary=boundary, runtime=runtime)

    async def _async_service_add_schedule(
        self,
        days: list[str],
        start: str,
        duration: int,
        boundary: bool | None = None,
    ) -> None:
        """Add one or more schedule entries."""
        await async_handle_add_schedule(
            self,
            days=days,
            start=start,
            duration=duration,
            boundary=boundary,
        )

    async def _async_service_edit_schedule(
        self,
        current_day: str,
        day: str,
        start: str,
        duration: int,
        current_start: str | None = None,
        boundary: bool | None = None,
    ) -> None:
        """Replace one schedule entry."""
        await async_handle_edit_schedule(
            self,
            current_day=current_day,
            day=day,
            start=start,
            duration=duration,
            current_start=current_start,
            boundary=boundary,
        )

    async def _async_service_delete_schedule(
        self,
        all_schedules: bool = False,
        day: str | None = None,
        start: str | None = None,
    ) -> None:
        """Delete one schedule entry."""
        await async_handle_delete_schedule(
            self,
            all_schedules=all_schedules,
            day=day,
            start=start,
        )
