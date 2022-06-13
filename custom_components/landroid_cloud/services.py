"""Services definitions."""
from __future__ import annotations
from dataclasses import dataclass
from functools import partial
import json
from typing import cast

from homeassistant.const import CONF_ENTITY_ID, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.util.read_only_dict import ReadOnlyDict

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

            api: LandroidAPI = await async_match_api(hass, device)

            if isinstance(api, type(None)):
                LOGGER.write(
                    LoggerType.SERVICE_CALL,
                    "Couldn't match a device with device_id = %s",
                    device.id,
                    log_level=LogLevel.ERROR,
                )
                return

            await api.services[service]["service"](service_data)

            # if service == SERVICE_CONFIG:
            #     await async_set_new_config(api, service_data)
            # elif service == SERVICE_EDGECUT:
            #     await async_edgecut(api, service_data)

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


async def async_set_new_config(api: LandroidAPI, data: ReadOnlyDict) -> None:
    """Set config parameters."""
    tmpdata = {}
    device: WorxCloud = api.device

    if "raindelay" in data:
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Setting raindelayto %s minutes",
            data["raindelay"],
        )
        tmpdata["rd"] = int(data["raindelay"])

    if "timeextension" in data:
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Setting timeextension to %s%%",
            data["timeextension"],
        )
        tmpdata["sc"] = {}
        tmpdata["sc"]["p"] = int(data["timeextension"])

    if "multizone_distances" in data:
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Setting multizone distances to %s",
            data["multizone_distances"],
        )
        sections = [
            int(x)
            for x in data["multizone_distances"]
            .replace("[", "")
            .replace("]", "")
            .split(",")
        ]
        if len(sections) != 4:
            raise HomeAssistantError("Incorrect format for multizone distances array")

        tmpdata["mz"] = sections

    if "multizone_probabilities" in data:
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Setting multizone probabilities to %s",
            data["multizone_probabilities"],
        )
        tmpdata["mzv"] = []
        sections = [
            int(x)
            for x in data["multizone_probabilities"]
            .replace("[", "")
            .replace("]", "")
            .split(",")
        ]
        if len(sections) != 4:
            raise HomeAssistantError(
                "Incorrect format for multizone probabilities array"
            )
        if not sum(sections) in [100, 0]:
            raise HomeAssistantError(
                "Sum of zone probabilities array MUST be 100"
                f"or 0 (disabled), request was: {sum(sections)}"
            )

        if sum(sections) == 0:
            for _ in range(10):
                tmpdata["mzv"].append(0)
        else:
            for idx, val in enumerate(sections):
                share = int(int(val) / 10)
                for _ in range(share):
                    tmpdata["mzv"].append(idx)

    if tmpdata:
        data = json.dumps(tmpdata)
        LOGGER.write(LoggerType.SERVICE_CALL, "New config: %s", data)
        # await api.hass.async_add_executor_job(partial(device.send, data))
