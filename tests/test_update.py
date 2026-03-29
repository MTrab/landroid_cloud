"""Tests for Landroid firmware update entities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.update import UpdateEntityFeature
from homeassistant.exceptions import HomeAssistantError
from pyworxcloud.exceptions import NotFoundError

from custom_components.landroid_cloud.update import (
    LandroidFirmwareUpdateEntity,
    NoFirmwareAvailableError,
    async_setup_entry,
    _release_notes_markdown,
)


def _make_entity(
    *,
    firmware: dict | None = None,
    info: dict | None = None,
    start_firmware_upgrade: AsyncMock | None = None,
) -> LandroidFirmwareUpdateEntity:
    """Create a lightweight update entity for unit tests."""
    entity = object.__new__(LandroidFirmwareUpdateEntity)
    entity._serial_number = "serial"
    entity.entity_description = SimpleNamespace(key="firmware")
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                serial_number="serial",
                online=True,
                firmware=firmware or {"version": "3.30"},
            )
        },
        cloud=SimpleNamespace(
            start_firmware_upgrade=start_firmware_upgrade or AsyncMock(),
        ),
        firmware_update_info=lambda _serial_number: info or {},
        async_update_listeners=lambda: None,
    )
    return entity


def test_update_entity_reports_versions_and_auto_update() -> None:
    """Firmware update entity should expose installed/latest versions."""
    entity = _make_entity(
        firmware={"version": "3.30", "auto_upgrade": True},
        info={"latest_version": "3.31", "auto_upgrade": True},
    )

    assert entity.installed_version == "3.30"
    assert entity.latest_version == "3.31"
    assert entity.auto_update is True


def test_update_entity_uses_installed_version_when_no_update_exists() -> None:
    """Latest version should fall back to the installed version."""
    entity = _make_entity(
        firmware={"version": "3.30", "auto_upgrade": False},
        info={"update_available": False},
    )

    assert entity.latest_version == "3.30"


def test_update_entity_reports_queued_upgrade_as_in_progress() -> None:
    """Queued upgrades should be represented as in progress."""
    entity = _make_entity(
        firmware={
            "version": "3.30",
            "upgrade": {"command_queued": True},
        },
    )

    assert entity.in_progress is True


def test_update_entity_supports_install_and_release_notes() -> None:
    """Firmware entity should expose install and release notes support."""
    entity = _make_entity()

    assert entity.supported_features == (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    )


def test_release_notes_markdown_includes_product_and_head_sections() -> None:
    """Release notes should include both product and head changelogs."""
    notes = _release_notes_markdown(
        {
            "product": {"version": "3.31", "changelog": "Main firmware fixes"},
            "head": {"version": "1.02", "changelog": "Head firmware fixes"},
        }
    )

    assert notes == (
        "## Product firmware 3.31\n\nMain firmware fixes\n\n"
        "## Head firmware 1.02\n\nHead firmware fixes"
    )


@pytest.mark.asyncio
async def test_async_install_queues_firmware_upgrade() -> None:
    """Installing should queue the latest firmware update."""
    start_firmware_upgrade = AsyncMock()
    listeners = Mock()
    entity = _make_entity(
        firmware={"version": "3.30"},
        info={"latest_version": "3.31"},
        start_firmware_upgrade=start_firmware_upgrade,
    )
    entity.coordinator.async_update_listeners = listeners

    await entity.async_install(version=None, backup=False)

    start_firmware_upgrade.assert_awaited_once_with("serial")
    listeners.assert_called_once_with()


@pytest.mark.asyncio
async def test_async_install_rejects_non_latest_versions() -> None:
    """Specific-version installs should only allow the advertised latest version."""
    entity = _make_entity(
        firmware={"version": "3.30"},
        info={"latest_version": "3.31"},
    )

    with pytest.raises(HomeAssistantError, match="Only the latest firmware version"):
        await entity.async_install(version="3.29", backup=False)


@pytest.mark.asyncio
async def test_async_install_surfaces_no_firmware_available() -> None:
    """Firmware availability errors should surface as Home Assistant errors."""
    entity = _make_entity(
        firmware={"version": "3.30"},
        info={"latest_version": "3.31"},
        start_firmware_upgrade=AsyncMock(
            side_effect=NoFirmwareAvailableError("No firmware available")
        ),
    )

    with pytest.raises(
        HomeAssistantError, match="No firmware update is currently available"
    ):
        await entity.async_install(version=None, backup=False)


@pytest.mark.asyncio
async def test_async_setup_entry_skips_devices_without_firmware_endpoint() -> None:
    """Update setup should skip mowers where the firmware endpoint returns 404."""
    entities = []

    def _async_add_entities(new_entities) -> None:
        entities.extend(new_entities)

    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(
            coordinator=SimpleNamespace(
                data={"serial": SimpleNamespace()},
                async_get_firmware_update_info=AsyncMock(side_effect=NotFoundError()),
            )
        )
    )

    await async_setup_entry(SimpleNamespace(), entry, _async_add_entities)

    assert entities == []
