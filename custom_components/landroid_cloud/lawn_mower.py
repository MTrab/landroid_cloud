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
from .const import (
    MOWER_STATE_EDGECUT,
    MOWER_STATE_ESCAPED_DIGITAL_FENCE,
    MOWER_STATE_IDLE,
    MOWER_STATE_RAIN_DELAY,
    MOWER_STATE_SEARCHING_ZONE,
    MOWER_STATE_STARTING,
    MOWER_STATE_ZONING,
)
from .services import (
    async_handle_add_schedule,
    async_handle_delete_schedule,
    async_handle_edit_schedule,
    async_handle_ots,
    async_register_entity_services,
)

STATUS_ACTIVITY_MAP: Final[dict[int, str]] = {
    0: MOWER_STATE_IDLE,
    1: LawnMowerActivity.DOCKED,
    2: MOWER_STATE_STARTING,
    3: MOWER_STATE_STARTING,
    4: LawnMowerActivity.RETURNING,
    5: LawnMowerActivity.RETURNING,
    6: LawnMowerActivity.RETURNING,
    7: LawnMowerActivity.MOWING,
    8: LawnMowerActivity.ERROR,
    9: LawnMowerActivity.ERROR,
    10: LawnMowerActivity.ERROR,
    11: LawnMowerActivity.ERROR,
    12: LawnMowerActivity.MOWING,
    13: MOWER_STATE_ESCAPED_DIGITAL_FENCE,
    30: LawnMowerActivity.RETURNING,
    31: MOWER_STATE_ZONING,
    32: MOWER_STATE_EDGECUT,
    33: MOWER_STATE_STARTING,
    34: LawnMowerActivity.PAUSED,
    103: MOWER_STATE_SEARCHING_ZONE,
    104: LawnMowerActivity.RETURNING,
}
MOWER_DESCRIPTION: Final = LawnMowerEntityEntityDescription(
    key="mower", translation_key="mower"
)
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
    def activity(self) -> str | None:
        """Return current mower activity."""
        rain_remaining = getattr(
            getattr(self.device, "rainsensor", {}), "get", lambda *_: None
        )("remaining")
        if self.device.raindelay_active or (
            isinstance(rain_remaining, int) and rain_remaining > 0
        ):
            return MOWER_STATE_RAIN_DELAY

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
        *,
        duration: int,
        days: list[str] | None = None,
        day: str | None = None,
        start: str | None = None,
        boundary: bool | None = None,
    ) -> None:
        """Add one or more schedule entries."""
        await async_handle_add_schedule(
            self,
            days=days,
            day=day,
            start=start,
            duration=duration,
            boundary=boundary,
        )

    async def _async_service_edit_schedule(
        self,
        *,
        current_day: str,
        day: str,
        start: str | None,
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
        *,
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
