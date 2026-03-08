"""Tests for shared entity helpers."""

from types import SimpleNamespace

from custom_components.landroid_cloud.entity import _firmware_version


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
