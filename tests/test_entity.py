"""Tests for shared entity helpers."""

from types import SimpleNamespace

from custom_components.landroid_cloud.entity import (
    LandroidBaseEntity,
    device_coordinates,
    device_location_attributes,
    device_supports_location,
    _firmware_version,
)


def test_firmware_version_from_dict() -> None:
    """Firmware version should be read from dict-shaped payloads."""
    device = SimpleNamespace(firmware={"version": "3.45"})
    assert _firmware_version(device) == "3.45"


def test_firmware_version_from_object() -> None:
    """Firmware version should also support object attributes."""
    device = SimpleNamespace(firmware=SimpleNamespace(version="7.8.9"))
    assert _firmware_version(device) == "7.8.9"


def test_firmware_version_defaults_to_unknown() -> None:
    """Missing firmware data should return fallback."""
    device = SimpleNamespace(firmware=None)
    assert _firmware_version(device) == "unknown"


def test_device_coordinates_reads_mapping_values() -> None:
    """GPS coordinates should be normalized from mapping-like payloads."""
    device = SimpleNamespace(gps={"latitude": 51.5, "longitude": 5.1})

    assert device_coordinates(device) == (51.5, 5.1)


def test_device_location_attributes_returns_legacy_keys() -> None:
    """Legacy mower attributes should expose GPS coordinates unchanged."""
    device = SimpleNamespace(gps={"latitude": 51.5, "longitude": 5.1})

    assert device_location_attributes(device) == {
        "latitude": 51.5,
        "longitude": 5.1,
    }


def test_device_supports_location_checks_module_markers() -> None:
    """A 4G module marker should be enough to create a tracker entity."""
    device = SimpleNamespace(module_config={"4G": {}})

    assert device_supports_location(device) is True


class _ReadonlyEntity(LandroidBaseEntity):
    """Minimal readonly entity for availability tests."""


class _WritableEntity(LandroidBaseEntity):
    """Minimal writable entity for availability tests."""

    _attr_requires_online = True


def test_readonly_entity_stays_available_when_device_is_offline() -> None:
    """Readonly entities should stay available with cached offline data."""
    entity = object.__new__(_ReadonlyEntity)
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={"serial": SimpleNamespace(online=False)},
    )
    entity._serial_number = "serial"

    assert entity.available is True


def test_writable_entity_becomes_unavailable_when_device_is_offline() -> None:
    """Writable entities should be unavailable while device is offline."""
    entity = object.__new__(_WritableEntity)
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={"serial": SimpleNamespace(online=False)},
    )
    entity._serial_number = "serial"

    assert entity.available is False


def test_entities_are_unavailable_when_coordinator_data_is_stale() -> None:
    """Coordinator update failures should still mark all entities unavailable."""
    entity = object.__new__(_ReadonlyEntity)
    entity.coordinator = SimpleNamespace(
        last_update_success=False,
        data={"serial": SimpleNamespace(online=True)},
    )
    entity._serial_number = "serial"

    assert entity.available is False
