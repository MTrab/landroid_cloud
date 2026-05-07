"""Tests for mower device tracker entities."""

from types import SimpleNamespace

import pytest

from custom_components.landroid_cloud.device_tracker import (
    LandroidCloudLocationEntity,
    async_setup_entry,
)


def test_location_tracker_reports_coordinates() -> None:
    """GPS-capable mowers should expose coordinates through the tracker."""
    entity = object.__new__(LandroidCloudLocationEntity)
    entity._serial_number = "serial"
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                gps={"latitude": 51.815106289, "longitude": 5.855785009666666}
            )
        },
    )

    assert entity.available is True
    assert entity.name == "Location"
    assert entity.latitude == 51.815106289
    assert entity.longitude == 5.855785009666666
    assert entity.entity_registry_enabled_default is False


def test_location_tracker_is_unavailable_without_fix() -> None:
    """Trackers should wait for real coordinates before reporting state."""
    entity = object.__new__(LandroidCloudLocationEntity)
    entity._serial_number = "serial"
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={"serial": SimpleNamespace(module_status={"4G": {}}, gps={})},
    )

    assert entity.available is False
    assert entity.latitude is None
    assert entity.longitude is None


@pytest.mark.asyncio
async def test_async_setup_entry_only_adds_trackers_for_gps_capable_mowers() -> None:
    """Only mowers with a 4G/GPS module should create tracker entities."""
    added_entities = []
    coordinator = SimpleNamespace(
        data={
            "gps": SimpleNamespace(gps={"latitude": 1.0, "longitude": 2.0}),
            "module": SimpleNamespace(module_config={"4G": {}}),
            "plain": SimpleNamespace(),
        }
    )
    entry = SimpleNamespace(runtime_data=SimpleNamespace(coordinator=coordinator))

    def _async_add_entities(entities) -> None:
        added_entities.extend(list(entities))

    await async_setup_entry(None, entry, _async_add_entities)

    assert [entity._serial_number for entity in added_entities] == ["gps", "module"]
