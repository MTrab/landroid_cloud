"""Update platform for Landroid Cloud."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyworxcloud.exceptions import APIException, NoConnectionError, OfflineError

try:
    from pyworxcloud.exceptions import NoFirmwareAvailableError, NoFirmwareOtaError
except ImportError:

    class NoFirmwareOtaError(Exception):
        """Fallback for older pyworxcloud versions without OTA exception support."""

    class NoFirmwareAvailableError(Exception):
        """Fallback for older pyworxcloud versions without OTA exception support."""


from .entity import LandroidBaseEntity

_LOGGER = logging.getLogger(__name__)


def _firmware_dict(device) -> dict[str, Any]:
    """Return firmware metadata as a dict when available."""
    firmware = getattr(device, "firmware", None)
    return firmware if isinstance(firmware, dict) else {}


def _normalized_version(value: Any) -> str | None:
    """Return a clean version string or None when unavailable."""
    if value is None:
        return None
    version = str(value).strip()
    if not version or version.lower() == "unknown":
        return None
    return version


def _changelog_text(value: Any) -> str | None:
    """Return changelog text from either a raw string or localized dict."""
    if isinstance(value, str):
        text = value.strip()
        return text or None

    if isinstance(value, dict):
        english = value.get("en")
        if isinstance(english, str) and english.strip():
            return english.strip()

        for localized in value.values():
            if isinstance(localized, str) and localized.strip():
                return localized.strip()

    return None


def _latest_firmware_info(device, cached_info: dict[str, Any] | None) -> dict[str, Any]:
    """Merge cached upgrade metadata with the latest device firmware payload."""
    merged = dict(cached_info or {})
    firmware = _firmware_dict(device)
    upgrade = firmware.get("upgrade")
    if isinstance(upgrade, dict):
        merged.update(upgrade)

    for source_key, target_key in (
        ("auto_upgrade", "auto_upgrade"),
        ("latest_version", "latest_version"),
        ("mandatory", "mandatory"),
        ("ota_supported", "ota_supported"),
        ("update_available", "update_available"),
        ("upgrade_failed", "upgrade_failed"),
        ("version", "current_version"),
    ):
        value = firmware.get(source_key)
        if value is not None:
            merged[target_key] = value

    return merged


def _release_summary(info: dict[str, Any]) -> str | None:
    """Return a short changelog summary when available."""
    product = info.get("product")
    if isinstance(product, dict):
        if changelog := _changelog_text(product.get("changelog")):
            return changelog[:255]

    head = info.get("head")
    if isinstance(head, dict):
        if changelog := _changelog_text(head.get("changelog")):
            return changelog[:255]

    return None


def _release_notes_markdown(info: dict[str, Any]) -> str | None:
    """Build markdown release notes from firmware metadata."""
    sections: list[str] = []

    product = info.get("product")
    if isinstance(product, dict):
        version = _normalized_version(product.get("version")) or "Unknown"
        if changelog := _changelog_text(product.get("changelog")):
            sections.append(f"## Product firmware {version}\n\n{changelog}")

    head = info.get("head")
    if isinstance(head, dict):
        version = _normalized_version(head.get("version")) or "Unknown"
        if changelog := _changelog_text(head.get("changelog")):
            sections.append(f"## Head firmware {version}\n\n{changelog}")

    if not sections:
        return None

    return "\n\n".join(sections)


@dataclass(frozen=True, kw_only=True)
class LandroidUpdateDescription(UpdateEntityDescription):
    """Description for Landroid update entities."""


UPDATES: tuple[LandroidUpdateDescription, ...] = (
    LandroidUpdateDescription(
        key="firmware",
        translation_key="firmware",
        device_class=UpdateDeviceClass.FIRMWARE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Landroid Cloud update entities."""
    del hass
    coordinator = entry.runtime_data.coordinator
    entities: list[LandroidFirmwareUpdateEntity] = []

    for serial_number in coordinator.data:
        try:
            info = await coordinator.async_get_firmware_update_info(serial_number)
        except (
            APIException,
            NoConnectionError,
            OfflineError,
            ValueError,
        ) as err:
            _LOGGER.debug(
                "Unable to preload firmware update info for %s: %s",
                serial_number,
                err,
            )
            info = {}

        if info.get("ota_supported") is False:
            continue

        entities.extend(
            LandroidFirmwareUpdateEntity(
                coordinator=coordinator,
                config_entry=entry,
                serial_number=serial_number,
                description=description,
            )
            for description in UPDATES
        )

    async_add_entities(entities)


class LandroidFirmwareUpdateEntity(LandroidBaseEntity, UpdateEntity):
    """Representation of a Landroid firmware update entity."""

    entity_description: LandroidUpdateDescription
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    )

    def __init__(
        self,
        coordinator,
        config_entry,
        serial_number: str,
        description: LandroidUpdateDescription,
    ) -> None:
        """Initialize the update entity."""
        self.entity_description = description
        super().__init__(
            coordinator, config_entry, serial_number, self.entity_description.key
        )

    async def async_added_to_hass(self) -> None:
        """Fetch firmware metadata when the entity is added."""
        await super().async_added_to_hass()
        if not self.coordinator.firmware_update_info(self._serial_number):
            try:
                await self.coordinator.async_refresh_firmware_update_info(
                    self._serial_number
                )
            except (
                APIException,
                NoConnectionError,
                OfflineError,
                ValueError,
            ) as err:
                _LOGGER.debug(
                    "Unable to fetch firmware update info for %s: %s",
                    self._serial_number,
                    err,
                )

    async def async_update(self) -> None:
        """Refresh firmware metadata for this mower."""
        await self.coordinator.async_refresh_firmware_update_info(self._serial_number)

    @property
    def _info(self) -> dict[str, Any]:
        """Return merged firmware update metadata for the mower."""
        return _latest_firmware_info(
            self.device,
            self.coordinator.firmware_update_info(self._serial_number),
        )

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        return _normalized_version(_firmware_dict(self.device).get("version"))

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        latest_version = _normalized_version(self._info.get("latest_version"))
        if latest_version is not None:
            return latest_version
        return self.installed_version

    @property
    def auto_update(self) -> bool:
        """Indicate if the mower has automatic firmware updates enabled."""
        value = self._info.get("auto_upgrade")
        return bool(value) if isinstance(value, bool) else False

    @property
    def in_progress(self) -> bool:
        """Return whether an OTA command has been queued."""
        value = self._info.get("command_queued")
        return bool(value) if isinstance(value, bool) else False

    @property
    def release_summary(self) -> str | None:
        """Return a short changelog excerpt."""
        return _release_summary(self._info)

    async def async_release_notes(self) -> str | None:
        """Return full markdown release notes when available."""
        try:
            info = await self.coordinator.async_refresh_firmware_update_info(
                self._serial_number
            )
        except (
            APIException,
            NoConnectionError,
            OfflineError,
            ValueError,
        ) as err:
            _LOGGER.debug(
                "Unable to refresh firmware release notes for %s: %s",
                self._serial_number,
                err,
            )
            info = self._info
        else:
            info = _latest_firmware_info(self.device, info)

        notes = _release_notes_markdown(info)
        _LOGGER.debug(
            "Firmware release notes requested for %s (%s): available=%s",
            getattr(self.device, "name", self._serial_number),
            self._serial_number,
            notes is not None,
        )
        return notes

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Queue the firmware update."""
        del backup, kwargs
        serial_number = str(self.device.serial_number)
        latest_version = self.latest_version

        if version is not None and version != latest_version:
            raise HomeAssistantError(
                f"Only the latest firmware version can be installed ({latest_version})"
            )

        _LOGGER.debug(
            "Firmware update triggered for %s (%s): installed=%s latest=%s",
            getattr(self.device, "name", serial_number),
            serial_number,
            self.installed_version,
            latest_version,
        )

        try:
            await self.coordinator.cloud.start_firmware_upgrade(serial_number)
        except NoFirmwareOtaError as err:
            raise HomeAssistantError(
                "This mower does not support OTA firmware upgrades"
            ) from err
        except NoFirmwareAvailableError as err:
            raise HomeAssistantError(
                "No firmware update is currently available"
            ) from err
        except (NoConnectionError, OfflineError) as err:
            raise HomeAssistantError("Mower is unavailable") from err
        except APIException as err:
            raise HomeAssistantError("Cloud command failed") from err

        self.coordinator.async_update_listeners()
