"""Services definitions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import cast

from homeassistant.const import CONF_ENTITY_ID, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry

from pyworxcloud import WorxCloud

from .api import LandroidAPI
from .const import (
    DOMAIN,
    LOGLEVEL,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_OTS,
    SERVICE_PARTYMODE,
    SERVICE_RESTART,
    SERVICE_SCHEDULE,
    SERVICE_SETZONE,
    SERVICE_TORQUE,
    LandroidFeatureSupport,
)
from .scheme import (
    CONFIG_SCHEMA,
    EMPTY_SCHEME,
    OTS_SCHEME,
    SCHEDULE_SCHEME,
    SET_ZONE_SCHEME,
    TORQUE_SCHEME,
)
from .utils.logger import LandroidLogger, LogLevel, LoggerType

LOGGER = LandroidLogger(__name__, LOGLEVEL)


@dataclass
class LandroidServiceDescription:
    """A class that describes Home Assistant entities."""

    # This is the key identifier for this entity
    key: str
    feature: LandroidFeatureSupport | None = None
    schema: str = EMPTY_SCHEME


SUPPORTED_SERVICES = [
    LandroidServiceDescription(
        key=SERVICE_CONFIG, schema=CONFIG_SCHEMA, feature=LandroidFeatureSupport.CONFIG
    ),
    LandroidServiceDescription(
        key=SERVICE_PARTYMODE, feature=LandroidFeatureSupport.PARTYMODE
    ),
    LandroidServiceDescription(
        key=SERVICE_SETZONE,
        schema=SET_ZONE_SCHEME,
        feature=LandroidFeatureSupport.SETZONE,
    ),
    LandroidServiceDescription(key=SERVICE_LOCK, feature=LandroidFeatureSupport.LOCK),
    LandroidServiceDescription(
        key=SERVICE_RESTART, feature=LandroidFeatureSupport.RESTART
    ),
    LandroidServiceDescription(
        key=SERVICE_EDGECUT, feature=LandroidFeatureSupport.EDGECUT
    ),
    LandroidServiceDescription(
        key=SERVICE_OTS, schema=OTS_SCHEME, feature=LandroidFeatureSupport.OTS
    ),
    LandroidServiceDescription(
        key=SERVICE_SCHEDULE,
        schema=SCHEDULE_SCHEME,
        feature=LandroidFeatureSupport.SCHEDULES,
    ),
    LandroidServiceDescription(
        key=SERVICE_TORQUE, schema=TORQUE_SCHEME, feature=LandroidFeatureSupport.TORQUE
    ),
]


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Landroid Cloud integration."""

    async def async_call_landroid_service(service_call: ServiceCall) -> None:
        """Call correct Landroid Cloud service."""
        service = service_call.service
        service_data = service_call.data

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        devices: DeviceEntry = []

        if CONF_DEVICE_ID in service_data:
            for entry in service_data[CONF_DEVICE_ID]:
                devices.append(device_registry.async_get(entry))
        else:
            for entry in service_data[CONF_ENTITY_ID]:
                devices.append(
                    device_registry.async_get(
                        entity_registry.entities.get(entry).device_id
                    )
                )

        for device in devices:
            api: LandroidAPI = await async_match_api(hass, device)

            if isinstance(api, type(None)):
                LOGGER.write(
                    LoggerType.SERVICE_CALL,
                    "Couldn't match a device with device_id = %s",
                    device.id,
                    log_level=LogLevel.ERROR,
                )
                return

            if not service in api.services:
                LOGGER.write(
                    LoggerType.SERVICE_CALL,
                    "The called service, %s, is not supported by this device!",
                    service,
                    log_level=LogLevel.ERROR,
                )
                return False

            if not api.device.online:
                LOGGER.write(
                    LoggerType.SERVICE_CALL,
                    "Device is offline, can't send command.",
                    log_level=LogLevel.ERROR,
                )
                return False

            await api.services[service]["service"](service_data)

    for service in SUPPORTED_SERVICES:
        if not hass.services.has_service(DOMAIN, service.key):
            LOGGER.write(LoggerType.SERVICE_ADD, "Adding %s", service.key)
            hass.services.async_register(
                DOMAIN,
                service.key,
                async_call_landroid_service,
                schema=service.schema,
            )


async def async_match_api(hass: HomeAssistant, device: DeviceEntry) -> WorxCloud | None:
    """Match device to API."""
    for possible_entry in hass.data[DOMAIN].values():
        if device.id in possible_entry["device_ids"]:
            for possible_device in possible_entry.values():
                if not isinstance(possible_device, dict):
                    continue  # This property isn't a dict, so we are skipping
                if not "api" in possible_device:
                    continue  # This dict doesn't contain the property api, so we are skipping
                check_api = cast(LandroidAPI, possible_device["api"])
                if check_api.device_id == device.id:
                    return check_api

    return None
