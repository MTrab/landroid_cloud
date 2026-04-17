"""Tests for Landroid switches."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.landroid_cloud.switch import LandroidSwitch, SWITCHES


def test_switches_are_configuration_entities() -> None:
    """All switch entities should be categorized as configuration."""
    assert all(
        description.entity_category is EntityCategory.CONFIG for description in SWITCHES
    )


def test_party_mode_is_disabled_by_default() -> None:
    """Party mode should be disabled by default."""
    party_mode = next(
        description for description in SWITCHES if description.key == "party_mode"
    )

    assert party_mode.entity_registry_enabled_default is False


def test_auto_schedule_switch_is_disabled_by_default() -> None:
    """Auto schedule should be disabled by default."""
    auto_schedule = next(
        description for description in SWITCHES if description.key == "auto_schedule"
    )

    assert auto_schedule.entity_registry_enabled_default is False


def test_firmware_auto_update_switch_is_disabled_by_default() -> None:
    """Firmware auto update should be disabled by default."""
    firmware_auto_update = next(
        description
        for description in SWITCHES
        if description.key == "firmware_auto_update"
    )

    assert firmware_auto_update.entity_registry_enabled_default is False


def test_irrigation_and_exclude_nights_are_disabled_by_default() -> None:
    """Auto-schedule switches should be disabled by default."""
    irrigation = next(
        description for description in SWITCHES if description.key == "irrigation"
    )
    exclude_nights = next(
        description for description in SWITCHES if description.key == "exclude_nights"
    )

    assert irrigation.entity_registry_enabled_default is False
    assert exclude_nights.entity_registry_enabled_default is False


def test_acs_is_disabled_by_default() -> None:
    """ACS should be disabled by default."""
    acs = next(description for description in SWITCHES if description.key == "acs")

    assert acs.entity_registry_enabled_default is False


def test_cut_over_border_switch_is_disabled_by_default() -> None:
    """Cut over border should be disabled by default."""
    description = next(
        description for description in SWITCHES if description.key == "cut_over_border"
    )

    assert description.entity_registry_enabled_default is False
    assert description.requires_protocol == 1


def test_auto_schedule_dependent_switch_is_unavailable_when_disabled() -> None:
    """Dependent auto-schedule switches should be unavailable when disabled."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description for description in SWITCHES if description.key == "irrigation"
    )
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = True
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                online=True,
                schedules={"auto_schedule": {"enabled": False, "settings": {}}},
            )
        },
    )

    assert entity.available is False


def test_firmware_auto_update_reads_firmware_flag() -> None:
    """Firmware auto update should read its state from firmware metadata."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description
        for description in SWITCHES
        if description.key == "firmware_auto_update"
    )
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = False
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "serial": SimpleNamespace(
                online=True,
                firmware={"auto_upgrade": True},
            )
        },
    )

    assert entity.is_on is True


@pytest.mark.asyncio
async def test_firmware_auto_update_calls_cloud_command() -> None:
    """Firmware auto update should call the dedicated cloud API method."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description
        for description in SWITCHES
        if description.key == "firmware_auto_update"
    )
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = False
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(set_firmware_auto_upgrade=AsyncMock()),
        data={
            "serial": SimpleNamespace(serial_number="serial", online=True, firmware={})
        },
    )

    await entity.async_turn_on()

    entity.coordinator.cloud.set_firmware_auto_upgrade.assert_awaited_once_with(
        "serial", True
    )


def test_cut_over_border_reads_cached_border_cut_setting() -> None:
    """Cut over border should read the cached pyworxcloud setting."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description for description in SWITCHES if description.key == "cut_over_border"
    )
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = False
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(
            get_border_cut_settings=lambda _serial: {"cut_over_border": False}
        ),
        last_update_success=True,
        data={"serial": SimpleNamespace(serial_number="serial", online=True)},
    )

    assert entity.is_on is False


@pytest.mark.asyncio
async def test_cut_over_border_calls_border_cut_settings_writer() -> None:
    """Cut over border should call the dedicated border-cut settings API method."""
    entity = object.__new__(LandroidSwitch)
    entity._serial_number = "serial"
    entity.entity_description = next(
        description for description in SWITCHES if description.key == "cut_over_border"
    )
    entity._attr_requires_online = True
    entity._attr_requires_auto_schedule = False
    entity.coordinator = SimpleNamespace(
        cloud=SimpleNamespace(set_border_cut_settings=AsyncMock()),
        data={"serial": SimpleNamespace(serial_number="serial", online=True)},
    )

    await entity.async_turn_on()

    entity.coordinator.cloud.set_border_cut_settings.assert_awaited_once_with(
        "serial",
        cut_over_border=True,
    )
