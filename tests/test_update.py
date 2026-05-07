"""Tests for Landroid firmware update entities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.update import UpdateEntityFeature
from homeassistant.exceptions import HomeAssistantError
from pyworxcloud.exceptions import OfflineError

from custom_components.landroid_cloud.update import (
    LandroidFirmwareUpdateEntity,
    NoFirmwareAvailableError,
    _changelog_text,
    _release_notes_markdown,
)


def _make_entity(
    *,
    firmware: dict | None = None,
    info: dict | None = None,
    start_firmware_upgrade: AsyncMock | None = None,
    refresh_firmware_update_info: AsyncMock | None = None,
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
        async_refresh_firmware_update_info=(
            refresh_firmware_update_info or AsyncMock(return_value=info or {})
        ),
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


def test_update_entity_stays_available_when_mower_is_offline() -> None:
    """Firmware update entity should stay available with cached metadata offline."""
    entity = _make_entity()
    entity.coordinator.data["serial"].online = False

    assert entity.available is True


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


def test_release_notes_markdown_prefers_markdown_payload() -> None:
    """Markdown release notes should prefer changelog_markdown when available."""
    notes = _release_notes_markdown(
        {
            "product": {
                "version": "3.31",
                "changelog": {"en": "Plain text notes"},
                "changelog_markdown": {"en": "## Markdown notes"},
            }
        }
    )

    assert notes == "## Product firmware 3.31\n\n## Markdown notes"


def test_changelog_text_prefers_english_from_localized_dict() -> None:
    """Localized changelog dicts should prefer English text."""
    assert _changelog_text({"da": "Danske noter", "en": "English notes"}) == (
        "English notes"
    )


def test_release_summary_supports_localized_changelog_dict() -> None:
    """Release summary should support pyworxcloud changelog dict payloads."""
    entity = _make_entity(
        info={
            "product": {
                "version": "3.31",
                "changelog": {"en": "Main firmware fixes", "da": "Firmware rettelser"},
            }
        }
    )

    assert entity.release_summary == "Main firmware fixes"


def test_release_summary_uses_changelog_excerpt() -> None:
    """Release summary should expose the short changelog excerpt."""
    entity = _make_entity(
        info={
            "product": {
                "version": "3.31",
                "changelog": "Main firmware fixes and stability improvements",
            }
        }
    )

    assert entity.release_summary == "Main firmware fixes and stability improvements"


@pytest.mark.asyncio
async def test_async_release_notes_returns_markdown() -> None:
    """Release notes should be exposed through the update entity API."""
    refresh_firmware_update_info = AsyncMock(
        return_value={
            "product": {
                "version": "3.31",
                "changelog": {"en": "Main firmware fixes"},
                "changelog_markdown": {"en": "## Main firmware fixes"},
            },
            "head": {
                "version": "1.02",
                "changelog": {"en": "Head firmware fixes"},
                "changelog_markdown": {"en": "## Head firmware fixes"},
            },
        }
    )
    entity = _make_entity(
        info={
            "product": {
                "version": "3.31",
                "changelog": {"en": "Main firmware fixes"},
                "changelog_markdown": {"en": "## Main firmware fixes"},
            },
            "head": {
                "version": "1.02",
                "changelog": {"en": "Head firmware fixes"},
                "changelog_markdown": {"en": "## Head firmware fixes"},
            },
        },
        refresh_firmware_update_info=refresh_firmware_update_info,
    )

    assert await entity.async_release_notes() == (
        "## Product firmware 3.31\n\n## Main firmware fixes\n\n"
        "## Head firmware 1.02\n\n## Head firmware fixes"
    )
    refresh_firmware_update_info.assert_awaited_once_with("serial")


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
async def test_async_install_ignores_offline_race_when_started_online() -> None:
    """Transient offline races should not fail a queued install started online."""
    listeners = Mock()
    entity = _make_entity(
        firmware={"version": "3.30"},
        info={"latest_version": "3.31"},
        start_firmware_upgrade=AsyncMock(
            side_effect=OfflineError(
                "The device is currently offline, no action was sent."
            )
        ),
    )
    entity.coordinator.async_update_listeners = listeners

    await entity.async_install(version=None, backup=False)

    listeners.assert_called_once_with()


@pytest.mark.asyncio
async def test_async_install_surfaces_offline_when_started_offline() -> None:
    """Offline installs should still fail when the mower was already offline."""
    entity = _make_entity(
        firmware={"version": "3.30"},
        info={"latest_version": "3.31"},
        start_firmware_upgrade=AsyncMock(
            side_effect=OfflineError(
                "The device is currently offline, no action was sent."
            )
        ),
    )
    entity.coordinator.data["serial"].online = False

    with pytest.raises(HomeAssistantError, match="Mower is unavailable"):
        await entity.async_install(version=None, backup=False)
