"""Custom lawn mower entity services for Landroid Cloud."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import HomeAssistantError
from pyworxcloud import ScheduleEntry, ScheduleModel
from pyworxcloud.day_map import DAY_MAP
from pyworxcloud.exceptions import NoOneTimeScheduleError
from pyworxcloud.utils.schedule_codec import (
    add_schedule_entry as add_schedule_entry_model,
)

from .commands import async_run_cloud_command

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import EntityPlatform

    from .lawn_mower import LandroidCloudMowerEntity

SERVICE_OTS: Final = "ots"
SERVICE_ADD_SCHEDULE: Final = "add_schedule"
SERVICE_EDIT_SCHEDULE: Final = "edit_schedule"
SERVICE_DELETE_SCHEDULE: Final = "delete_schedule"
ATTR_BOUNDARY: Final = "boundary"
ATTR_ALL_SCHEDULES: Final = "all_schedules"
ATTR_CURRENT_DAY: Final = "current_day"
ATTR_CURRENT_START: Final = "current_start"
ATTR_DAY: Final = "day"
ATTR_DAYS: Final = "days"
ATTR_DURATION: Final = "duration"
ATTR_RUNTIME: Final = "runtime"
ATTR_START: Final = "start"
DAYS: Final = tuple(DAY_MAP[index] for index in sorted(DAY_MAP))


def _normalize_day(day: str | None, field_name: str) -> str:
    """Validate and normalize a weekday value."""
    if not isinstance(day, str):
        raise HomeAssistantError(f"{field_name} must be one of: {', '.join(DAYS)}")

    normalized_day = day.lower()
    if normalized_day not in DAYS:
        raise HomeAssistantError(f"{field_name} must be one of: {', '.join(DAYS)}")

    return normalized_day


def _normalize_start(start: str | None, field_name: str) -> str:
    """Validate and normalize a HH:MM start value."""
    if not isinstance(start, str):
        raise HomeAssistantError(f"{field_name} must be in HH:MM format")

    parts = start.split(":")
    if len(parts) != 2:
        raise HomeAssistantError(f"{field_name} must be in HH:MM format")

    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as err:
        raise HomeAssistantError(f"{field_name} must be in HH:MM format") from err

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise HomeAssistantError(f"{field_name} must be in HH:MM format")

    return f"{hour:02d}:{minute:02d}"


def _normalize_add_schedule_days(
    *, day: str | None = None, days: list[str] | None = None
) -> list[str]:
    """Return a unique, validated list of weekdays for add_schedule."""
    resolved_days: list[str] = []
    if days is not None:
        resolved_days.extend(days)
    if day is not None:
        resolved_days.append(day)

    normalized_days = [
        _normalize_day(value, ATTR_DAY) for value in dict.fromkeys(resolved_days)
    ]
    if not normalized_days:
        raise HomeAssistantError("Select at least one day for the schedule")

    return normalized_days


def async_register_entity_services(platform: EntityPlatform) -> None:
    """Register custom lawn mower entity services."""
    platform.async_register_entity_service(
        SERVICE_OTS,
        {
            vol.Required(ATTR_BOUNDARY): bool,
            vol.Required(ATTR_RUNTIME): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=120)
            ),
        },
        "_async_service_ots",
    )
    add_schedule_schema = {
        vol.Optional(ATTR_DAY): cv.string,
        vol.Optional(ATTR_DAYS): vol.All(
            cv.ensure_list, [vol.In(DAYS)], vol.Length(min=1)
        ),
        vol.Required(ATTR_START): vol.Any(cv.string, None),
        vol.Required(ATTR_DURATION): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_BOUNDARY): vol.Any(bool, None),
    }
    schedule_entry_schema = {
        vol.Required(ATTR_START): vol.Any(cv.string, None),
        vol.Required(ATTR_DURATION): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_BOUNDARY): vol.Any(bool, None),
    }
    platform.async_register_entity_service(
        SERVICE_ADD_SCHEDULE,
        add_schedule_schema,
        "_async_service_add_schedule",
    )
    platform.async_register_entity_service(
        SERVICE_EDIT_SCHEDULE,
        {
            vol.Required(ATTR_CURRENT_DAY): vol.In(DAYS),
            vol.Optional(ATTR_CURRENT_START): vol.Any(cv.string, None),
            vol.Required(ATTR_DAY): vol.In(DAYS),
            **schedule_entry_schema,
        },
        "_async_service_edit_schedule",
    )
    platform.async_register_entity_service(
        SERVICE_DELETE_SCHEDULE,
        {
            vol.Optional(ATTR_ALL_SCHEDULES): vol.Any(bool, None),
            vol.Optional(ATTR_DAY): vol.In(DAYS),
            vol.Optional(ATTR_START): vol.Any(cv.string, None),
        },
        "_async_service_delete_schedule",
    )


async def async_handle_ots(
    entity: LandroidCloudMowerEntity, *, boundary: bool, runtime: int
) -> None:
    """Handle legacy OTS service call."""
    try:
        await async_run_cloud_command(
            lambda: entity.coordinator.cloud.ots(
                str(entity.device.serial_number), boundary, runtime
            )
        )
    except HomeAssistantError as err:
        if isinstance(err.__cause__, NoOneTimeScheduleError):
            raise HomeAssistantError(
                "Mower does not support one-time schedule"
            ) from err
        raise


def _build_schedule_entry(
    entity: LandroidCloudMowerEntity,
    *,
    entry_id: str,
    day: str,
    start: str,
    duration: int,
    boundary: bool | None = None,
    source: str | None = None,
) -> ScheduleEntry:
    """Build a normalized schedule entry from service parameters."""
    day = _normalize_day(day, ATTR_DAY)
    start = _normalize_start(start, ATTR_START)
    protocol = entity.coordinator.cloud.get_schedule(
        str(entity.device.serial_number)
    ).protocol
    if protocol == 0:
        if boundary is None:
            boundary = False
        resolved_source = source or "primary"
        secondary = resolved_source == "secondary"
    else:
        resolved_source = "slot"
        secondary = False

    return ScheduleEntry(
        entry_id=entry_id,
        day=day,
        start=start,
        duration=duration,
        boundary=boundary,
        source=resolved_source,
        secondary=secondary,
    )


def _schedule_for_write(entity: LandroidCloudMowerEntity) -> ScheduleModel:
    """Return the normalized schedule used for service writes."""
    return entity.coordinator.cloud.get_schedule(str(entity.device.serial_number))


def _resolve_protocol_zero_source(
    entity: LandroidCloudMowerEntity,
    *,
    day: str,
    entries: list[ScheduleEntry] | None = None,
    keep_entry_id: str | None = None,
    preferred_source: str | None = None,
) -> str | None:
    """Resolve which two-slot source should be used for a day."""
    schedule = _schedule_for_write(entity)
    if schedule.protocol != 0:
        return None

    normalized_day = _normalize_day(day, ATTR_DAY)
    pool = entries if entries is not None else getattr(schedule, "entries", [])
    day_entries = [
        entry
        for entry in pool
        if entry.day == normalized_day and entry.entry_id != keep_entry_id
    ]
    has_primary = any(entry.source == "primary" for entry in day_entries)
    has_secondary = any(entry.source == "secondary" for entry in day_entries)

    if preferred_source == "primary" and not has_primary:
        return "primary"
    if preferred_source == "secondary" and not has_secondary:
        return "secondary"
    if not has_primary:
        return "primary"
    if not has_secondary:
        return "secondary"
    raise HomeAssistantError(
        "This day already has two schedules; delete one before adding another"
    )


def _resolve_schedule_entry(
    entity: LandroidCloudMowerEntity,
    *,
    day: str,
    start: str | None = None,
    action: str,
) -> ScheduleEntry:
    """Resolve one schedule entry from a day and optional start time."""
    normalized_day = _normalize_day(day, ATTR_DAY)
    normalized_start = None if start is None else _normalize_start(start, ATTR_START)
    entries = [
        entry
        for entry in getattr(_schedule_for_write(entity), "entries", [])
        if entry.day == normalized_day
    ]

    if not entries:
        raise HomeAssistantError("No schedule entry exists for the selected day")

    if len(entries) == 1:
        if normalized_start is not None and entries[0].start != normalized_start:
            raise HomeAssistantError(
                "No schedule entry matches the selected day and start time"
            )
        return entries[0]

    if normalized_start is None:
        raise HomeAssistantError(
            f"Select a start time to choose which schedule to {action}"
        )

    entries = [entry for entry in entries if entry.start == normalized_start]
    if not entries:
        raise HomeAssistantError(
            "No schedule entry matches the selected day and start time"
        )
    if len(entries) > 1:
        raise HomeAssistantError(
            "More than one schedule uses that day and start time; change one of them first"
        )
    return entries[0]


def _resolve_delete_schedule_entry_id(
    entity: LandroidCloudMowerEntity,
    *,
    day: str,
    start: str | None = None,
) -> str:
    """Resolve one entry to delete using simple user-facing selectors."""
    return _resolve_schedule_entry(
        entity,
        day=day,
        start=start,
        action="delete",
    ).entry_id


def _build_cleared_schedule(entity: LandroidCloudMowerEntity) -> ScheduleModel:
    """Return the current schedule model with all entries removed."""
    schedule = _schedule_for_write(entity)
    return ScheduleModel(
        enabled=schedule.enabled,
        time_extension=schedule.time_extension,
        entries=[],
        protocol=schedule.protocol,
    )


async def async_handle_add_schedule(
    entity: LandroidCloudMowerEntity,
    *,
    days: list[str] | None = None,
    day: str | None = None,
    start: str | None = None,
    duration: int,
    boundary: bool | None = None,
) -> None:
    """Add one or more schedule entries."""
    serial_number = str(entity.device.serial_number)
    schedule = _schedule_for_write(entity)
    updated_schedule = schedule
    normalized_days = _normalize_add_schedule_days(day=day, days=days)
    normalized_start = _normalize_start(start, ATTR_START)

    try:
        for resolved_day in normalized_days:
            source = _resolve_protocol_zero_source(
                entity,
                day=resolved_day,
                entries=updated_schedule.entries,
            )
            updated_schedule = add_schedule_entry_model(
                updated_schedule,
                _build_schedule_entry(
                    entity,
                    entry_id="",
                    day=resolved_day,
                    start=normalized_start,
                    duration=duration,
                    boundary=boundary,
                    source=source,
                ),
            )
    except ValueError as err:
        raise HomeAssistantError(str(err)) from err

    await async_run_cloud_command(
        lambda: entity.coordinator.cloud.set_schedule(serial_number, updated_schedule)
    )


async def async_handle_edit_schedule(
    entity: LandroidCloudMowerEntity,
    *,
    current_day: str,
    day: str,
    start: str | None,
    duration: int,
    current_start: str | None = None,
    boundary: bool | None = None,
) -> None:
    """Replace one schedule entry."""
    serial_number = str(entity.device.serial_number)
    current_entry = _resolve_schedule_entry(
        entity,
        day=current_day,
        start=current_start,
        action="edit",
    )
    normalized_day = _normalize_day(day, ATTR_DAY)
    source = _resolve_protocol_zero_source(
        entity,
        day=normalized_day,
        keep_entry_id=current_entry.entry_id,
        preferred_source=(
            current_entry.source if current_entry.day == normalized_day else None
        ),
    )
    await async_run_cloud_command(
        lambda: entity.coordinator.cloud.update_schedule_entry(
            serial_number,
            current_entry.entry_id,
            _build_schedule_entry(
                entity,
                entry_id=current_entry.entry_id,
                day=normalized_day,
                start=start,
                duration=duration,
                boundary=boundary,
                source=source,
            ),
        )
    )


async def async_handle_delete_schedule(
    entity: LandroidCloudMowerEntity,
    *,
    all_schedules: bool = False,
    day: str | None = None,
    start: str | None = None,
) -> None:
    """Delete one schedule entry."""
    serial_number = str(entity.device.serial_number)
    if all_schedules:
        await async_run_cloud_command(
            lambda: entity.coordinator.cloud.set_schedule(
                serial_number, _build_cleared_schedule(entity)
            )
        )
        return

    if day is None:
        raise HomeAssistantError(
            "Select a day or enable all schedules to delete everything"
        )
    resolved_entry_id = _resolve_delete_schedule_entry_id(
        entity,
        day=day,
        start=start,
    )
    await async_run_cloud_command(
        lambda: entity.coordinator.cloud.delete_schedule_entry(
            serial_number, resolved_entry_id
        )
    )
