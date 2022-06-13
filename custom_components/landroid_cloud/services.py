"""Services definitions."""
from __future__ import annotations
from dataclasses import dataclass

from homeassistant.const import CONF_ENTITY_ID, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry

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
)
from .scheme import (
    CONFIG_SCHEMA,
    EMPTY_SCHEME,
    OTS_SCHEME,
    SCHEDULE_SCHEME,
    SET_ZONE_SCHEME,
    TORQUE_SCHEME,
)
from .utils.logger import LandroidLogger, LoggerType

LOGGER = LandroidLogger(__name__, LOGLEVEL)


@dataclass
class LandroidServiceDescription:
    """A class that describes Home Assistant entities."""

    # This is the key identifier for this entity
    key: str
    service: str
    schema: str = EMPTY_SCHEME


SUPPORTED_SERVICES = [
    LandroidServiceDescription(
        key=SERVICE_CONFIG, service="async_config", schema=CONFIG_SCHEMA
    ),
    LandroidServiceDescription(key=SERVICE_PARTYMODE, service="async_toggle_partymode"),
    LandroidServiceDescription(
        key=SERVICE_SETZONE, service="async_toggle_partymode", schema=SET_ZONE_SCHEME
    ),
    LandroidServiceDescription(key=SERVICE_LOCK, service="async_toggle_lock"),
    LandroidServiceDescription(key=SERVICE_RESTART, service="async_restart"),
    LandroidServiceDescription(key=SERVICE_EDGECUT, service="async_edgecut"),
    LandroidServiceDescription(key=SERVICE_OTS, service="async_ots", schema=OTS_SCHEME),
    LandroidServiceDescription(
        key=SERVICE_SCHEDULE, service="async_set_schedule", schema=SCHEDULE_SCHEME
    ),
    LandroidServiceDescription(
        key=SERVICE_TORQUE, service="async_set_torque", schema=TORQUE_SCHEME
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
        # entity_entries = async_entries_for_config_entry(entity_registry, entry.entry_id)

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
            LOGGER.write(
                LoggerType.SERVICE_REGISTER,
                "Received %s service call with service_data '%s' "
                "to device '%s' identified by device_id '%s'",
                service,
                service_data,
                device.name,
                device.id,
            )

    for service in SUPPORTED_SERVICES:
        if not hass.services.has_service(DOMAIN, service.key):
            LOGGER.write(LoggerType.SERVICE_ADD, "Adding %s", service.key)
            hass.services.async_register(
                DOMAIN,
                service.key,
                async_call_landroid_service,
                schema=service.schema,
            )
