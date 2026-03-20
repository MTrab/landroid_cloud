"""Tests for mower activity mapping."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.exceptions import HomeAssistantError
import pytest
from pyworxcloud import ScheduleEntry, ScheduleModel

from custom_components.landroid_cloud.const import (
    MOWER_STATE_EDGECUT,
    MOWER_STATE_ESCAPED_DIGITAL_FENCE,
    MOWER_STATE_IDLE,
    MOWER_STATE_SEARCHING_ZONE,
    MOWER_STATE_STARTING,
    MOWER_STATE_ZONING,
)
from custom_components.landroid_cloud.lawn_mower import (
    LandroidCloudMowerEntity,
    STATUS_ACTIVITY_MAP,
    SERVICE_ADD_SCHEDULE,
    SERVICE_DELETE_SCHEDULE,
    SERVICE_EDIT_SCHEDULE,
    SERVICE_OTS,
    async_setup_entry,
)


def test_start_sequence_states_map_to_starting() -> None:
    """Start-sequence related status codes should map to the restored starting state."""
    assert STATUS_ACTIVITY_MAP[2] == MOWER_STATE_STARTING
    assert STATUS_ACTIVITY_MAP[3] == MOWER_STATE_STARTING
    assert STATUS_ACTIVITY_MAP[33] == MOWER_STATE_STARTING


def test_restored_legacy_states_are_exposed() -> None:
    """Legacy mower states should map to dedicated mower activities again."""
    assert STATUS_ACTIVITY_MAP[0] == MOWER_STATE_IDLE
    assert STATUS_ACTIVITY_MAP[13] == MOWER_STATE_ESCAPED_DIGITAL_FENCE
    assert STATUS_ACTIVITY_MAP[31] == MOWER_STATE_ZONING
    assert STATUS_ACTIVITY_MAP[32] == MOWER_STATE_EDGECUT
    assert STATUS_ACTIVITY_MAP[103] == MOWER_STATE_SEARCHING_ZONE


def test_unknown_state_defaults_to_error() -> None:
    """Unknown status ids should not map to non-standard activities."""
    assert (
        STATUS_ACTIVITY_MAP.get(999, LawnMowerActivity.ERROR) is LawnMowerActivity.ERROR
    )


@pytest.mark.asyncio
async def test_ots_service_calls_cloud_ots() -> None:
    """OTS service should call the cloud command with legacy arguments."""
    entity = object.__new__(LandroidCloudMowerEntity)
    entity._serial_number = "serial"
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(ots=AsyncMock()),
        data={"serial": SimpleNamespace(serial_number="serial")},
    )

    await entity._async_service_ots(boundary=True, runtime=45)

    entity.coordinator.cloud.ots.assert_awaited_once_with("serial", True, 45)


def _entity_with_cloud(protocol: int = 0) -> LandroidCloudMowerEntity:
    """Return a minimally initialized mower entity for service tests."""
    schedule = _schedule_model(protocol=protocol, entries=[])
    entity = object.__new__(LandroidCloudMowerEntity)
    entity._serial_number = "serial"
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(
            ots=AsyncMock(),
            add_schedule_entry=AsyncMock(),
            set_schedule=AsyncMock(),
            update_schedule_entry=AsyncMock(),
            delete_schedule_entry=AsyncMock(),
            get_schedule=lambda serial_number: schedule,
        ),
        data={"serial": SimpleNamespace(serial_number="serial")},
    )
    return entity


def _schedule_model(
    *, protocol: int, entries: list[ScheduleEntry]
) -> ScheduleModel:
    """Build a normalized schedule model for tests."""
    return ScheduleModel(
        enabled=False,
        time_extension=0 if protocol == 0 else None,
        entries=entries,
        protocol=protocol,
    )


@pytest.mark.asyncio
async def test_add_schedule_service_calls_cloud_add_schedule_entry() -> None:
    """Add schedule should persist one selected day through one schedule update."""
    entity = _entity_with_cloud(protocol=0)

    await entity._async_service_add_schedule(
        days=["monday"],
        start="09:00",
        duration=60,
        boundary=False,
    )

    entity.coordinator.cloud.set_schedule.assert_awaited_once()
    serial_number, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert serial_number == "serial"
    assert schedule == ScheduleModel(
        enabled=False,
        time_extension=0,
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            )
        ],
    )


@pytest.mark.asyncio
async def test_add_schedule_service_accepts_day_alias() -> None:
    """Add schedule should accept the legacy single-day alias."""
    entity = _entity_with_cloud(protocol=1)

    await entity._async_service_add_schedule(
        day="tuesday",
        start="12:00",
        duration=50,
        boundary=None,
    )

    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries == [
        ScheduleEntry(
            entry_id="p1:0",
            day="tuesday",
            start="12:00",
            duration=50,
            boundary=None,
            source="slot",
            secondary=False,
        )
    ]


@pytest.mark.asyncio
async def test_add_schedule_service_rejects_invalid_start_with_clear_error() -> None:
    """Add schedule should fail with a Home Assistant error for malformed time."""
    entity = _entity_with_cloud(protocol=0)

    with pytest.raises(HomeAssistantError, match="start must be in HH:MM format"):
        await entity._async_service_add_schedule(
            days=["monday"],
            start="25:00",
            duration=30,
        )


@pytest.mark.asyncio
async def test_add_schedule_service_uses_secondary_when_primary_exists() -> None:
    """Add schedule should use the second slot when the first one is already taken."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            )
        ],
    )

    await entity._async_service_add_schedule(
        days=["monday"],
        start="12:00",
        duration=45,
        boundary=True,
    )

    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries == [
        ScheduleEntry(
            entry_id="p0:monday:primary",
            day="monday",
            start="09:00",
            duration=60,
            boundary=False,
            source="primary",
            secondary=False,
        ),
        ScheduleEntry(
            entry_id="p0:monday:secondary",
            day="monday",
            start="12:00",
            duration=45,
            boundary=True,
            source="secondary",
            secondary=True,
        ),
    ]


@pytest.mark.asyncio
async def test_add_schedule_service_raises_when_day_is_full() -> None:
    """Add schedule should fail clearly when both slots on a day are already used."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p0:monday:secondary",
                day="monday",
                start="13:00",
                duration=45,
                boundary=True,
                source="secondary",
                secondary=True,
            ),
        ],
    )

    with pytest.raises(
        HomeAssistantError,
        match="This day already has two schedules; delete one before adding another",
    ):
        await entity._async_service_add_schedule(
            days=["monday"],
            start="15:00",
            duration=30,
            boundary=True,
        )


@pytest.mark.asyncio
async def test_add_schedule_service_allows_multiple_protocol_one_slots_per_day() -> None:
    """Add schedule should allow another same-day entry on multi-slot mowers."""
    entity = _entity_with_cloud(protocol=1)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=1,
        entries=[
            ScheduleEntry(
                entry_id="p1:0",
                day="monday",
                start="09:00",
                duration=60,
                boundary=None,
                source="slot",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p1:1",
                day="monday",
                start="13:00",
                duration=45,
                boundary=None,
                source="slot",
                secondary=False,
            ),
        ],
    )

    await entity._async_service_add_schedule(
        days=["monday"],
        start="16:00",
        duration=30,
    )

    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries[-1] == ScheduleEntry(
        entry_id="p1:2",
        day="monday",
        start="16:00",
        duration=30,
        boundary=None,
        source="slot",
        secondary=False,
    )


@pytest.mark.asyncio
async def test_add_schedule_service_supports_multiple_days_in_one_call() -> None:
    """Add schedule should create one entry per selected day in a single update."""
    entity = _entity_with_cloud(protocol=0)

    await entity._async_service_add_schedule(
        days=["monday", "wednesday"],
        start="09:00",
        duration=60,
        boundary=False,
    )

    entity.coordinator.cloud.set_schedule.assert_awaited_once()
    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries == [
        ScheduleEntry(
            entry_id="p0:monday:primary",
            day="monday",
            start="09:00",
            duration=60,
            boundary=False,
            source="primary",
            secondary=False,
        ),
        ScheduleEntry(
            entry_id="p0:wednesday:primary",
            day="wednesday",
            start="09:00",
            duration=60,
            boundary=False,
            source="primary",
            secondary=False,
        ),
    ]


@pytest.mark.asyncio
async def test_edit_schedule_service_calls_cloud_update_schedule_entry() -> None:
    """Edit schedule should resolve the current entry from day and start."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            )
        ],
    )

    await entity._async_service_edit_schedule(
        current_day="monday",
        day="monday",
        start="10:00",
        duration=45,
        boundary=True,
        current_start="09:00",
    )

    entity.coordinator.cloud.update_schedule_entry.assert_awaited_once()
    serial_number, entry_id, entry = (
        entity.coordinator.cloud.update_schedule_entry.await_args.args
    )
    assert serial_number == "serial"
    assert entry_id == "p0:monday:primary"
    assert entry == ScheduleEntry(
        entry_id="p0:monday:primary",
        day="monday",
        start="10:00",
        duration=45,
        boundary=True,
        source="primary",
        secondary=False,
    )


@pytest.mark.asyncio
async def test_edit_schedule_service_reassigns_free_slot_on_new_day() -> None:
    """Edit should choose the free target-day slot when moving a two-slot schedule."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:secondary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="secondary",
                secondary=True,
            ),
            ScheduleEntry(
                entry_id="p0:tuesday:primary",
                day="tuesday",
                start="08:00",
                duration=30,
                boundary=False,
                source="primary",
                secondary=False,
            ),
        ],
    )

    await entity._async_service_edit_schedule(
        current_day="monday",
        current_start="09:00",
        day="tuesday",
        start="10:00",
        duration=45,
        boundary=True,
    )

    _, entry_id, entry = entity.coordinator.cloud.update_schedule_entry.await_args.args
    assert entry_id == "p0:monday:secondary"
    assert entry == ScheduleEntry(
        entry_id="p0:monday:secondary",
        day="tuesday",
        start="10:00",
        duration=45,
        boundary=True,
        source="secondary",
        secondary=True,
    )


@pytest.mark.asyncio
async def test_edit_schedule_service_raises_when_target_day_is_full() -> None:
    """Edit should fail clearly when moving to a full two-slot day."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p0:tuesday:primary",
                day="tuesday",
                start="08:00",
                duration=30,
                boundary=False,
                source="primary",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p0:tuesday:secondary",
                day="tuesday",
                start="14:00",
                duration=45,
                boundary=True,
                source="secondary",
                secondary=True,
            ),
        ],
    )

    with pytest.raises(
        HomeAssistantError,
        match="This day already has two schedules; delete one before adding another",
    ):
        await entity._async_service_edit_schedule(
            current_day="monday",
            current_start="09:00",
            day="tuesday",
            start="10:00",
            duration=45,
            boundary=True,
        )


@pytest.mark.asyncio
async def test_delete_schedule_service_calls_cloud_delete_schedule_entry() -> None:
    """Delete schedule should resolve a same-day entry from day and start."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:secondary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="secondary",
                secondary=True,
            )
        ],
    )

    await entity._async_service_delete_schedule(
        day="monday",
        start="09:00",
    )

    entity.coordinator.cloud.delete_schedule_entry.assert_awaited_once_with(
        "serial", "p0:monday:secondary"
    )


@pytest.mark.asyncio
async def test_delete_schedule_service_can_clear_all_schedules() -> None:
    """Delete schedule should be able to clear all schedules in one call."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            )
        ],
    )

    await entity._async_service_delete_schedule(all_schedules=True)

    entity.coordinator.cloud.set_schedule.assert_awaited_once()
    serial_number, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert serial_number == "serial"
    assert schedule == ScheduleModel(
        enabled=False,
        time_extension=0,
        entries=[],
        protocol=0,
    )


@pytest.mark.asyncio
async def test_delete_schedule_service_raises_for_ambiguous_same_day_slots() -> None:
    """Delete should ask for start time when a day has multiple schedules."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p0:monday:secondary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=True,
                source="secondary",
                secondary=True,
            ),
        ],
    )

    with pytest.raises(HomeAssistantError, match="Select a start time"):
        await entity._async_service_delete_schedule(
            day="monday",
        )


@pytest.mark.asyncio
async def test_delete_schedule_service_requires_day_without_delete_all() -> None:
    """Delete schedule should require a day unless all schedules is selected."""
    entity = _entity_with_cloud(protocol=0)

    with pytest.raises(
        HomeAssistantError,
        match="Select a day or enable all schedules to delete everything",
    ):
        await entity._async_service_delete_schedule()


@pytest.mark.asyncio
async def test_delete_schedule_service_resolves_same_day_entry_by_start() -> None:
    """Delete should resolve same-day entries by start time when needed."""
    entity = _entity_with_cloud(protocol=1)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=1,
        entries=[
            ScheduleEntry(
                entry_id="p1:0",
                day="monday",
                start="09:00",
                duration=60,
                boundary=None,
                source="slot",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p1:1",
                day="monday",
                start="13:00",
                duration=45,
                boundary=None,
                source="slot",
                secondary=False,
            ),
        ],
    )

    await entity._async_service_delete_schedule(
        day="monday",
        start="13:00",
    )

    entity.coordinator.cloud.delete_schedule_entry.assert_awaited_once_with(
        "serial", "p1:1"
    )


@pytest.mark.asyncio
async def test_delete_schedule_service_raises_for_ambiguous_same_day_start() -> None:
    """Delete should ask for start time when a day has multiple schedules."""
    entity = _entity_with_cloud(protocol=1)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=1,
        entries=[
            ScheduleEntry(
                entry_id="p1:0",
                day="monday",
                start="09:00",
                duration=60,
                boundary=None,
                source="slot",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p1:1",
                day="monday",
                start="13:00",
                duration=45,
                boundary=None,
                source="slot",
                secondary=False,
            ),
        ],
    )

    with pytest.raises(HomeAssistantError, match="Select a start time"):
        await entity._async_service_delete_schedule(day="monday")


@pytest.mark.asyncio
async def test_delete_schedule_service_raises_for_duplicate_same_day_and_start() -> None:
    """Delete should fail clearly when two schedules share day and start time."""
    entity = _entity_with_cloud(protocol=0)
    entity.coordinator.cloud.get_schedule = lambda serial_number: _schedule_model(
        protocol=0,
        entries=[
            ScheduleEntry(
                entry_id="p0:monday:primary",
                day="monday",
                start="09:00",
                duration=60,
                boundary=False,
                source="primary",
                secondary=False,
            ),
            ScheduleEntry(
                entry_id="p0:monday:secondary",
                day="monday",
                start="09:00",
                duration=45,
                boundary=True,
                source="secondary",
                secondary=True,
            ),
        ],
    )

    with pytest.raises(
        HomeAssistantError,
        match="More than one schedule uses that day and start time",
    ):
        await entity._async_service_delete_schedule(day="monday", start="09:00")


@pytest.mark.asyncio
async def test_protocol_zero_schedule_defaults_boundary_to_false() -> None:
    """Protocol 0 schedule writes should default boundary to false."""
    entity = _entity_with_cloud(protocol=0)

    await entity._async_service_add_schedule(
        days=["monday"],
        start="09:00",
        duration=30,
    )

    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries == [
        ScheduleEntry(
            entry_id="p0:monday:primary",
            day="monday",
            start="09:00",
            duration=30,
            boundary=False,
            source="primary",
            secondary=False,
        )
    ]


@pytest.mark.asyncio
async def test_protocol_one_schedule_forces_slot_source() -> None:
    """Protocol 1 schedule writes should always use slot source."""
    entity = _entity_with_cloud(protocol=1)

    await entity._async_service_add_schedule(
        days=["tuesday"],
        start="12:00",
        duration=50,
    )

    _, schedule = entity.coordinator.cloud.set_schedule.await_args.args
    assert schedule.entries == [
        ScheduleEntry(
            entry_id="p1:0",
            day="tuesday",
            start="12:00",
            duration=50,
            boundary=None,
            source="slot",
            secondary=False,
        )
    ]


@pytest.mark.asyncio
async def test_async_setup_entry_registers_schedule_services(monkeypatch) -> None:
    """Setup should register OTS and schedule services on the mower platform."""
    registrations: list[tuple[str, str]] = []

    class FakePlatform:
        def async_register_entity_service(self, name, schema, method):
            del schema
            registrations.append((name, method))

    monkeypatch.setattr(
        "custom_components.landroid_cloud.lawn_mower.entity_platform.async_get_current_platform",
        lambda: FakePlatform(),
    )

    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(coordinator=SimpleNamespace(data={})),
    )

    await async_setup_entry(
        SimpleNamespace(),
        entry,
        lambda entities: None,
    )

    assert registrations == [
        (SERVICE_OTS, "_async_service_ots"),
        (SERVICE_ADD_SCHEDULE, "_async_service_add_schedule"),
        (SERVICE_EDIT_SCHEDULE, "_async_service_edit_schedule"),
        (SERVICE_DELETE_SCHEDULE, "_async_service_delete_schedule"),
    ]
