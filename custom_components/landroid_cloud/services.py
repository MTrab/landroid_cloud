"""Services definitions."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.const import CONF_DEVICE_ID, CONF_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .api import LandroidAPI
from .const import (
    ATTR_API,
    ATTR_DEVICEIDS,
    ATTR_DEVICES,
    ATTR_SERVICE,
    DOMAIN,
    LOGLEVEL,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_OTS,
    SERVICE_PARTYMODE,
    SERVICE_SETPARTYMODE,
    SERVICE_REFRESH,
    SERVICE_RESTART,
    SERVICE_SCHEDULE,
    SERVICE_SEND_RAW,
    SERVICE_SETZONE,
    SERVICE_TORQUE,
    LandroidFeatureSupport,
)
from .scheme import (
    CONFIG_SCHEMA,
    EMPTY_SCHEME,
    OTS_SCHEME,
    RAW_SCHEME,
    SCHEDULE_SCHEME,
    SET_ZONE_SCHEME,
    TORQUE_SCHEME,
    SET_PARTYMODE_SCHEME,
)
from .utils.logger import LandroidLogger, LoggerType


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
        key=SERVICE_SETPARTYMODE,
        schema=SET_PARTYMODE_SCHEME,
        feature=LandroidFeatureSupport.SETPARTYMODE,
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
    LandroidServiceDescription(
        key=SERVICE_REFRESH, feature=LandroidFeatureSupport.REFRESH
    ),
    LandroidServiceDescription(
        key=SERVICE_SEND_RAW, feature=LandroidFeatureSupport.CONFIG, schema=RAW_SCHEME
    ),
]


@callback
async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Landroid Cloud integration."""

    async def async_call_landroid_service(service_call: ServiceCall) -> None:
        """Call correct Landroid Cloud service."""
        service = service_call.service
        service_data = service_call.data

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        devices: DeviceEntry = []

        if CONF_DEVICE_ID in service_data:
            if isinstance(service_data[CONF_DEVICE_ID], str):
                devices.append(device_registry.async_get(service_data[CONF_DEVICE_ID]))
            else:
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
                raise HomeAssistantError(
                    f"Failed to call service '{service_call.service}'. Config entry for target not found"
                )

            if not service in api.services:
                raise HomeAssistantError(
                    f"Failed to call service '{service_call.service}'. "
                    "Service is not supported by this device."
                )

            if not api.device.online:
                raise HomeAssistantError(
                    f"Failed to call service '{service_call.service}'. "
                    "Device is currently offline."
                )

            await api.services[service][ATTR_SERVICE](service_data)

    logger = LandroidLogger(name=__name__, log_level=LOGLEVEL)
    for service in SUPPORTED_SERVICES:
        if not hass.services.has_service(DOMAIN, service.key):
            logger.log(LoggerType.SERVICE_ADD, "Adding %s", service.key)
            hass.services.async_register(
                DOMAIN,
                service.key,
                async_call_landroid_service,
                schema=service.schema,
            )


async def async_match_api(
    hass: HomeAssistant, device: DeviceEntry
) -> LandroidAPI | None:
    """Match device to API."""
    logger = LandroidLogger(name=__name__, log_level=LOGLEVEL)
    if not hasattr(device, "id"):
        raise HomeAssistantError("No valid device object was specified.")

    logger.log(LoggerType.SERVICE_CALL, "Trying to match ID '%s'", device.id)
    for possible_entry in hass.data[DOMAIN].values():
        if not ATTR_DEVICEIDS in possible_entry:
            continue
        device_ids = possible_entry[ATTR_DEVICEIDS]
        logger.log(
            LoggerType.SERVICE_CALL, "Checking for '%s' in %s", device.id, device_ids
        )
        for name, did in device_ids.items():
            logger.log(LoggerType.SERVICE_CALL, "Matching '%s' to '%s'", device.id, did)
            if did == device.id:
                logger.log(
                    LoggerType.SERVICE_CALL,
                    "Found a match for '%s' in '%s'",
                    device.id,
                    name,
                )
                return possible_entry[ATTR_DEVICES][name][ATTR_API]

    return None
