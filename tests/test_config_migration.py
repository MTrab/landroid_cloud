"""Tests for v6 to v7 config migration behavior."""

from __future__ import annotations

from types import MappingProxyType, SimpleNamespace

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState

from custom_components.landroid_cloud import async_migrate_entry, async_setup_entry
from custom_components.landroid_cloud.const import CONF_CLOUD, DEFAULT_CLOUD, DOMAIN


def _make_config_entry(
    *,
    entry_id: str,
    data: dict[str, object],
    unique_id: str | None,
    version: int = 1,
) -> ConfigEntry:
    """Build a lightweight config entry for migration tests."""
    return ConfigEntry(
        version=version,
        minor_version=0,
        domain=DOMAIN,
        title="Landroid Cloud",
        data=data,
        source="user",
        unique_id=unique_id,
        options={},
        subentries_data=(),
        discovery_keys=MappingProxyType({}),
        entry_id=entry_id,
        state=ConfigEntryState.NOT_LOADED,
    )


class _ConfigEntriesManager:
    """Capture config entry updates during migration."""

    def __init__(self, entries: list[ConfigEntry]) -> None:
        self._entries = entries
        self.updates: list[dict[str, object]] = []

    def async_entries(self, domain: str) -> list[ConfigEntry]:
        """Return entries for the requested domain."""
        return [entry for entry in self._entries if entry.domain == domain]

    def async_update_entry(self, entry: ConfigEntry, **kwargs) -> bool:
        """Apply updates in the same shape Home Assistant would."""
        self.updates.append(kwargs)
        if "data" in kwargs:
            object.__setattr__(entry, "data", MappingProxyType(dict(kwargs["data"])))
        if "unique_id" in kwargs:
            object.__setattr__(entry, "unique_id", kwargs["unique_id"])
        if "version" in kwargs:
            object.__setattr__(entry, "version", kwargs["version"])
        if "title" in kwargs:
            object.__setattr__(entry, "title", kwargs["title"])
        return True


@pytest.mark.asyncio
async def test_async_migrate_entry_moves_legacy_type_to_cloud_and_unique_id() -> None:
    """Old v6 entries should be migrated to the v7 data and unique id format."""
    entry = _make_config_entry(
        entry_id="entry-1",
        data={
            "email": "User@Example.com",
            "password": "secret",
            "type": "Worx",
        },
        unique_id="User@Example.com_Worx",
    )
    manager = _ConfigEntriesManager([entry])
    hass = SimpleNamespace(config_entries=manager)

    assert await async_migrate_entry(hass, entry) is True
    assert dict(entry.data) == {
        "email": "User@Example.com",
        "password": "secret",
        CONF_CLOUD: DEFAULT_CLOUD,
    }
    assert entry.unique_id == "user@example.com::worx"
    assert entry.version == 2
    assert manager.updates == [
        {
            "data": {
                "email": "User@Example.com",
                "password": "secret",
                CONF_CLOUD: DEFAULT_CLOUD,
            },
            "version": 2,
            "unique_id": "user@example.com::worx",
        }
    ]


@pytest.mark.asyncio
async def test_async_migrate_entry_defaults_cloud_and_skips_unique_id_conflict() -> None:
    """Migration should fall back to Worx and avoid unique id clashes."""
    entry = _make_config_entry(
        entry_id="entry-1",
        data={
            "email": "user@example.com",
            "password": "secret",
        },
        unique_id=None,
    )
    conflicting_entry = _make_config_entry(
        entry_id="entry-2",
        data={
            "email": "other@example.com",
            "password": "secret",
            CONF_CLOUD: "worx",
        },
        unique_id="user@example.com::worx",
        version=2,
    )
    manager = _ConfigEntriesManager([entry, conflicting_entry])
    hass = SimpleNamespace(config_entries=manager)

    assert await async_migrate_entry(hass, entry) is True
    assert dict(entry.data) == {
        "email": "user@example.com",
        "password": "secret",
        CONF_CLOUD: DEFAULT_CLOUD,
    }
    assert entry.unique_id is None
    assert entry.version == 2
    assert manager.updates == [
        {
            "data": {
                "email": "user@example.com",
                "password": "secret",
                CONF_CLOUD: DEFAULT_CLOUD,
            },
            "version": 2,
        }
    ]


@pytest.mark.asyncio
async def test_async_setup_entry_falls_back_to_legacy_type_field(monkeypatch) -> None:
    """Setup should continue to work when only the legacy type field exists."""
    captured: dict[str, object] = {}

    class FakeCloud:
        """Minimal WorxCloud stub for setup verification."""

        def __init__(
            self,
            email: str,
            password: str,
            cloud: str,
            *,
            tz: str,
            command_timeout: float,
        ) -> None:
            captured.update(
                {
                    "email": email,
                    "password": password,
                    "cloud": cloud,
                    "tz": tz,
                    "command_timeout": command_timeout,
                }
            )
            self.devices = {}

        async def authenticate(self) -> bool:
            return True

        async def connect(self) -> bool:
            return True

        async def disconnect(self) -> None:
            return None

    class FakeCoordinator:
        """Avoid touching the real coordinator in the setup test."""

        def __init__(self, hass, cloud) -> None:
            self.hass = hass
            self.cloud = cloud
            self.data = {}

        async def async_setup(self) -> None:
            return None

        async def async_config_entry_first_refresh(self) -> None:
            return None

        async def async_shutdown(self) -> None:
            return None

    async def _async_get_integration(_hass, _domain):
        return SimpleNamespace(version="7.0.0b1")

    async def _async_forward_entry_setups(_entry, _platforms):
        return True

    async def _async_prime_awsiot_metrics() -> None:
        return None

    entry = SimpleNamespace(
        data={
            "email": "user@example.com",
            "password": "secret",
            "type": "Kress",
        },
        options={},
        entry_id="entry-1",
        runtime_data=None,
        add_update_listener=lambda _callback: None,
        async_on_unload=lambda _callback: None,
    )
    hass = SimpleNamespace(
        config=SimpleNamespace(time_zone="UTC"),
        config_entries=SimpleNamespace(
            async_forward_entry_setups=_async_forward_entry_setups,
        ),
    )

    monkeypatch.setattr(
        "custom_components.landroid_cloud.async_get_integration",
        _async_get_integration,
    )
    monkeypatch.setattr(
        "custom_components.landroid_cloud.async_prime_awsiot_metrics",
        _async_prime_awsiot_metrics,
    )
    monkeypatch.setattr("custom_components.landroid_cloud.WorxCloud", FakeCloud)
    monkeypatch.setattr(
        "custom_components.landroid_cloud.LandroidCloudCoordinator",
        FakeCoordinator,
    )

    assert await async_setup_entry(hass, entry) is True
    assert captured == {
        "email": "user@example.com",
        "password": "secret",
        "cloud": "kress",
        "tz": "UTC",
        "command_timeout": 30.0,
    }
    assert entry.runtime_data.cloud is not None
    assert entry.runtime_data.coordinator.cloud is entry.runtime_data.cloud
