"""Define device classes."""

# pylint: disable=unused-argument,too-many-instance-attributes,too-many-lines
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_utils
from homeassistant.util import slugify as util_slugify
from pyworxcloud import DeviceCapability, WorxCloud
from pyworxcloud.exceptions import (
    NoConnectionError,
    NoOneTimeScheduleError,
    NoPartymodeError,
    ZoneNoProbability,
    ZoneNotDefined,
)
from pyworxcloud.utils import DeviceHandler

from .api import LandroidAPI
from .attribute_map import ATTR_MAP
from .const import (
    ATTR_BOUNDARY,
    ATTR_DEVICEIDS,
    ATTR_JSON,
    ATTR_LANDROIDFEATURES,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_RUNTIME,
    ATTR_SERVICE,
    DOMAIN,
    ENTITY_ID_FORMAT,
    PLATFORMS_SECONDARY,
    SCHEDULE_TO_DAY,
    SCHEDULE_TYPE_MAP,
    SERVICE_CONFIG,
    SERVICE_OTS,
    SERVICE_SCHEDULE,
    SERVICE_SEND_RAW,
    STATE_INITIALIZING,
    STATE_MAP,
    STATE_OFFLINE,
    STATE_RAINDELAY,
    STATE_RETURNING,
    UPDATE_SIGNAL,
    LandroidFeatureSupport,
)
from .utils.logger import LandroidLogger, LoggerType, LogLevel
from .utils.schedules import parseday, pass_thru

# Commonly supported features
SUPPORT_LANDROID_BASE = (
    LawnMowerEntityFeature.PAUSE
    | LawnMowerEntityFeature.DOCK
    | LawnMowerEntityFeature.START_MOWING
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


@dataclass
class LandroidBaseEntityDescriptionMixin:
    """Describes a basic Landroid entity."""

    # value_fn: Callable[[DeviceHandler], bool | str | int | float]
    value_fn: Callable[[WorxCloud], bool | str | int | float]


@dataclass
class LandroidButtonEntityDescription(ButtonEntityDescription):
    """Describes a Landroid button entity."""

    press_action: Callable[[LandroidAPI, str], None] = (None,)
    required_feature: LandroidFeatureSupport | None = None


@dataclass
class LandroidSensorEntityDescription(
    SensorEntityDescription, LandroidBaseEntityDescriptionMixin
):
    """Describes a Landroid sensor."""

    unit_fn: Callable[[WorxCloud], None] = None
    attributes: [] | None = None  # type: ignore


@dataclass
class LandroidBinarySensorEntityDescription(
    BinarySensorEntityDescription, LandroidBaseEntityDescriptionMixin
):
    """Describes a Landroid binary_sensor."""


@dataclass
class LandroidNumberEntityDescription(NumberEntityDescription):
    """Describes a Landroid number."""

    value_fn: Callable[[LandroidAPI], bool | str | int | float | None] = None
    command_fn: Callable[[LandroidAPI, str], None] = None
    required_protocol: int | None = None
    required_capability: DeviceCapability | None = None


@dataclass
class LandroidSwitchEntityDescription(
    SwitchEntityDescription, LandroidBaseEntityDescriptionMixin
):
    """Describes a Landroid switch."""

    command_fn: Callable[[WorxCloud], None] = None
    icon_on: str | None = None
    icon_off: str | None = None
    required_feature: LandroidFeatureSupport | None = None


@dataclass
class LandroidSelectEntityDescription(SelectEntityDescription):
    """Describes a Landroid select."""

    value_fn: Callable[[WorxCloud], bool | str | int | float | None] = None
    command_fn: Callable[[LandroidAPI, str], None] = None


class LandroidCloudBaseEntity(LandroidLogger):
    """Define a base Landroid Cloud entity class.

    Override these functions as needed by the specific device integration:
    async def async_edgecut(self,  data: dict|None = None) -> None:
    async def async_toggle_lock(self,  data: dict|None = None) -> None:
    async def async_toggle_partymode(self,  data: dict|None = None) -> None:
    async def async_restart(self,  data: dict|None = None) -> None:
    async def async_set_zone(self,  data: dict|None = None) -> None:
    async def async_config(self,  data: dict|None = None) -> None:
    async def async_ots(self,  data: dict|None = None) -> None:
    async def async_set_schedule(self,  data: dict|None = None) -> None:
    async def async_set_torque(self,  data: dict|None = None) -> None:
    """

    _battery_level: int | None = None
    _attr_state = STATE_INITIALIZING
    _attr_landroid_features: int | None = None

    def __init__(self, hass: HomeAssistant, api: LandroidAPI):
        """Init new base for a Landroid Cloud entity."""
        self._api = api
        self.hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name}")

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        self._attributes = {}
        self._unique_id = f"{self._api.device.serial_number}_{api.name}"
        self._serialnumber = self._api.device.serial_number
        self._icon = None
        self._name = f"{api.friendly_name}"
        self._mac = self._api.device.mac_address
        # self._connections = {(dr.CONNECTION_NETWORK_MAC, self._mac)}
        self._connections = {}
        self._features_known = 0
        self._attr_available = self._device.online

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            self._connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}

        super().__init__()

    @property
    def base_features(self) -> int:
        """Call to get the base features."""
        return None

    async def async_edgecut(self, data: dict | None = None) -> None:
        """Call to start edge cut task."""
        return None

    async def async_toggle_lock(self, data: dict | None = None) -> None:
        """Toggle lock state."""
        return None

    async def async_toggle_partymode(self, data: dict | None = None) -> None:
        """Toggle partymode."""
        return None

    async def async_restart(self, data: dict | None = None) -> None:
        """Restart baseboard OS."""
        return None

    async def async_set_zone(self, data: dict | None = None) -> None:
        """Set next zone."""
        return None

    async def async_config(self, data: dict | None = None) -> None:
        """Configure device."""
        return None

    async def async_ots(self, data: dict | None = None) -> None:
        """Start one-time-schedule."""
        return None

    async def async_set_schedule(self, data: dict | None = None) -> None:
        """Set cutting schedule."""
        return None

    async def async_set_torque(self, data: dict | None = None) -> None:
        """Set wheel torque."""
        return None

    async def async_send_raw(self, data: dict | None = None) -> None:
        """Send a raw command."""
        return None

    @staticmethod
    def get_ots_scheme() -> Any:
        """Return device specific OTS_SCHEME."""
        return None

    @staticmethod
    def get_config_scheme() -> Any:
        """Return device specific CONFIG_SCHEME."""
        return None

    @property
    def device_info(self):
        """Return device info."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(self._name),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if self._mac != "__UUID__":
            info.update({"connections": self._connections})

        return info

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        self.update_callback()

        if isinstance(self._api.device_id, type(None)):
            entity_reg: EntityRegistry = er.async_get(self.hass)
            entry = entity_reg.async_get(self.entity_id)
            self._api.device_id = entry.device_id
            if (
                self.hass.data[DOMAIN][self._api.entry_id][ATTR_DEVICEIDS][
                    self._device.name
                ]
                != entry.device_id
            ):
                self.hass.data[DOMAIN][self._api.entry_id][ATTR_DEVICEIDS].update(
                    {self._device.name: entry.device_id}
                )

        self.log(
            LoggerType.SETUP,
            "Connecting to dispatcher signal '%s'",
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
        )
        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.update_callback,
        )

    @callback
    def update_callback(self):
        """Handle base update callback."""
        return False

    @callback
    def update_selected_zone(self):
        """Update zone selections in select entity."""
        return False

    async def async_update(self):
        """Handle default async_update actions."""
        return

    @callback
    def register_services(self) -> None:
        """Register services."""
        self.log_set_name(__name__)
        self.log_set_api(self._api)

        self._api.check_features()

        if self._api.features == 0:
            self.log(
                LoggerType.SERVICE_REGISTER,
                "No services registred as feature flags is set to %s",
                self._api.features,
            )
            return

        if self._api.features == self._features_known:
            return  # No new features known

        self.log(
            LoggerType.SERVICE_REGISTER,
            "Registering services with feature flags set to %s",
            self._api.features,
        )

        if self._api.features & LandroidFeatureSupport.CONFIG:
            self._api.services[SERVICE_CONFIG] = {
                ATTR_SERVICE: self.async_config,
            }

        if self._api.features & LandroidFeatureSupport.OTS:
            self._api.services[SERVICE_OTS] = {
                ATTR_SERVICE: self.async_ots,
            }

        if self._api.features & LandroidFeatureSupport.SCHEDULES:
            self._api.services[SERVICE_SCHEDULE] = {
                ATTR_SERVICE: self.async_set_schedule,
            }

        if self._api.features & LandroidFeatureSupport.RAW:
            self._api.services[SERVICE_SEND_RAW] = {
                ATTR_SERVICE: self.async_send_raw,
            }

        self._features_known = self._api.features

    def data_update(self):
        """Update the device."""
        self._attr_available = self._device.online
        self.log_set_name(__name__)
        self.log_set_api(self._api)
        self.log(LoggerType.DATA_UPDATE, "Updating")

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]
        device: DeviceHandler = self._device

        data = {}

        for key, value in ATTR_MAP.items():
            if hasattr(device, key):
                if value == "mac_address" and getattr(device, key) == "__UUID__":
                    value = "uuid"
                    key = "uuid"

                if value == "blades" and (getattr(device, key))["total_on"] == 0:
                    continue

                self.log(
                    LoggerType.DATA_UPDATE,
                    "Mapping '%s': %s",
                    value,
                    getattr(device, key),
                )
                data[value] = getattr(device, key)
            else:
                self.log(LoggerType.DATA_UPDATE, "Mapping did not find '%s'", value)

        data[ATTR_LANDROIDFEATURES] = self._api.features

        if hasattr(device, "gps"):
            data.update(
                {
                    ATTR_LATITUDE: device.gps["latitude"],
                    ATTR_LONGITUDE: device.gps["longitude"],
                }
            )

        self._attributes.update(data)
        self._attributes.update(
            {"api connected": self._api.cloud.mqtt.client.is_connected()}
        )

        self._available = (
            device.online
            if device.error.id in [-1, 0]
            else (not bool(isinstance(device.error.id, type(None))))
        )
        state = STATE_INITIALIZING

        if not device.online:
            state = STATE_OFFLINE
        # elif not device.online and device.error.id in [-1, 0]:
        #     state = STATE_OFFLINE
        elif device.error.id is not None and device.error.id > 0:
            if device.error.id > 0 and device.error.id != 5:
                state = LawnMowerActivity.ERROR
            elif device.error.id == 5:
                state = STATE_RAINDELAY
        else:
            try:
                self.log(LoggerType.DEVELOP, "Status: %s", device.status)
                state = STATE_MAP[device.status.id]
            except KeyError:
                state = STATE_INITIALIZING

        self.log(LoggerType.DATA_UPDATE, "Online: %s", device.online)
        self.log(LoggerType.DATA_UPDATE, "State '%s'", state)
        self.log(
            LoggerType.DATA_UPDATE,
            "Last update: %s",
            device.last_status["timestamp"] if "last_status" in device else "No data",
        )
        self.log(LoggerType.DATA_UPDATE, "Attributes:\n%s", self._attributes)
        self._attr_state = state

        self._serialnumber = device.serial_number
        if "percent" in device.battery:
            self._battery_level = device.battery["percent"]

        self.register_services()


# class LandroidBase(Entity):
#     """Define a base for all Landroid entities."""

#     def __init__(
#         self,
#         api: LandroidAPI,
#         entity_description,
#         config: ConfigEntry,
#     ) -> None:
#         """Initialize the base class."""
#         super().__init__()
#         self._api = api
#         self._config = config
#         self.entity_description = entity_description

#         self._attr_unique_id = util_slugify(
#             f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
#         )
#         self._attr_should_poll = False

#         self._attr_device_info = {
#             "identifiers": {
#                 (
#                     DOMAIN,
#                     self._api.unique_id,
#                     self._api.entry_id,
#                     self._device.serial_number,
#                 )
#             },
#             "name": str(f"{self._api.friendly_name}"),
#             "sw_version": self._device.firmware["version"],
#             "manufacturer": self._api.config["type"].capitalize(),
#             "model": self._device.model,
#             "serial_number": self._device.serial_number,
#         }

#         if not isinstance(self._device.mac_address, type(None)) and self._device.mac_address != "__UUID__":
#             _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
#             self._attr_device_info.update({"connections": _connections})

#         self._attr_available = self._device.online


class LandroidCloudMowerBase(LandroidCloudBaseEntity, LawnMowerEntity):
    """Define a base Landroid Cloud mower class."""

    _battery_level: int | None = None
    _attr_state = STATE_INITIALIZING
    _attr_translation_key = DOMAIN

    async def async_added_to_hass(self):
        """Check data and register services when added to hass."""
        await super().async_added_to_hass()
        logger = LandroidLogger(name=__name__, api=self._api, log_level=LogLevel.DEBUG)
        logger.log(
            LoggerType.SETUP,
            "Features not assessed, calling assessment with base features at %s",
            self.base_features,
        )

        if not self._device.online:
            return False

        self._api.check_features(int(self.base_features))
        self._api.features_loaded = True
        while not self._api.features_loaded:
            self.log(
                LoggerType.FEATURE_ASSESSMENT,
                "Waiting for features to be fully loaded, before continuing",
            )

        self.register_services()

        self._attributes.update({"protocol": self._device.protocol})

        await self.hass.config_entries.async_forward_entry_setups(
            self._api.entry, PLATFORMS_SECONDARY
        )

    @property
    def extra_state_attributes(self) -> str:
        """Return sensor attributes."""
        return self._attributes

    @property
    def device_class(self) -> str:
        """Return the ID of the capability, to identify the entity for translations."""
        return f"{DOMAIN}__state"

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def battery_level(self) -> str:
        """Return the battery level of the lawn_mower cleaner."""
        return self._battery_level

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.online

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """Disable polling."""
        return False

    @property
    def state(self) -> str:
        """Return sensor state."""
        return self._attr_state

    @callback
    def update_callback(self) -> None:
        """Get new data and update state."""
        self.data_update()
        self._api.features_loaded = True
        self.schedule_update_ha_state()

    async def async_start_mowing(self) -> None:
        """Start or resume the task."""
        self.log(LoggerType.SERVICE_CALL, "Starting")
        try:
            await self.hass.async_add_executor_job(
                self._api.cloud.start, self._device.serial_number
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_pause(self) -> None:
        """Pause the mowing cycle."""
        self.log(LoggerType.SERVICE_CALL, "Pausing")
        try:
            await self.hass.async_add_executor_job(
                self._api.cloud.pause, self._device.serial_number
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_start_pause(self) -> None:
        """Toggle the state of the mower."""
        self.log(LoggerType.SERVICE_CALL, "Toggeling state")
        try:
            if LawnMowerActivity.MOWING in self.state:
                await self.async_pause()
            else:
                await self.async_start_mowing()
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_dock(self, **kwargs: Any) -> None:
        """Set the device to return to the dock."""
        if self.state not in [LawnMowerActivity.DOCKED, STATE_RETURNING]:
            self.log(LoggerType.SERVICE_CALL, "Going back to dock")
            try:
                # Try calling home (keep knives on while going home)
                await self.hass.async_add_executor_job(
                    self._api.cloud.home, self._device.serial_number
                )
                # Ensure we are going home, in case the safehome wasn't successful
                wait_start = time.time()
                while time.time() < wait_start + 15:
                    await asyncio.sleep(1)
                    if self.state in [STATE_RETURNING, LawnMowerActivity.DOCKED]:
                        break

                # Mower didn't start homing routine
                # Possibly the mower doesn't support homing with blades on
                # Issue safehome command
                if self.state not in [STATE_RETURNING, LawnMowerActivity.DOCKED]:
                    await self.hass.async_add_executor_job(
                        self._api.cloud.safehome, self._device.serial_number
                    )
            except NoConnectionError as exc:
                raise ConfigEntryNotReady() from exc

    async def async_stop(self, **kwargs: Any) -> None:
        """Alias for return to base function."""
        await self.async_dock()

    async def async_set_zone(self, data: dict | None = None) -> None:
        """Set next zone to cut."""
        zone = data["zone"]
        try:
            self.log(LoggerType.SERVICE_CALL, "Setting zone to %s", zone)
            await self.hass.async_add_executor_job(
                partial(self._api.cloud.setzone, self._device.serial_number, str(zone))
            )
        except ZoneNotDefined:
            raise HomeAssistantError("The requested zone is not defined") from None
        except ZoneNoProbability:
            raise HomeAssistantError(
                "The requested zone has no probability set"
            ) from None
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_set_schedule(self, data: dict | None = None) -> None:
        """Set or change the schedule."""
        try:
            schedule_type = data["type"]
            schedule = {}
            if schedule_type == "secondary":
                # We are handling a secondary schedule
                # Insert primary schedule in dataset befor generating secondary
                schedule[SCHEDULE_TYPE_MAP["primary"]] = pass_thru(
                    self._device.schedules["primary"]
                )

            schedule[SCHEDULE_TYPE_MAP[schedule_type]] = []
            self.log(LoggerType.SERVICE_CALL, "Generating %s schedule", schedule_type)
            for day in SCHEDULE_TO_DAY.items():
                day = day[1]
                if day["start"] in data:
                    # Found day in dataset, generating an update to the schedule
                    if day["end"] not in data:
                        raise HomeAssistantError(
                            f"No end time specified for {day['clear']}"
                        )
                    schedule[SCHEDULE_TYPE_MAP[schedule_type]].append(
                        parseday(day, data)
                    )
                else:
                    # Didn't find day in dataset, parsing existing thru
                    current = []
                    current.append(
                        self._device.schedules[schedule_type][day["clear"]]["start"]
                    )
                    current.append(
                        self._device.schedules[schedule_type][day["clear"]]["duration"]
                    )
                    current.append(
                        int(
                            self._device.schedules[schedule_type][day["clear"]][
                                "boundary"
                            ]
                        )
                    )
                    schedule[SCHEDULE_TYPE_MAP[schedule_type]].append(current)

            if schedule_type == "primary" and "secondary" in self._device.schedules:
                # We are generating a primary schedule
                # To keep a secondary schedule we need to pass this thru to the dataset
                schedule[SCHEDULE_TYPE_MAP["secondary"]] = pass_thru(
                    self._device.schedules["secondary"]
                )

            data = json.dumps({"sc": schedule})
            self.log(
                LoggerType.SERVICE_CALL, "New %s schedule, %s", schedule_type, data
            )
            await self.hass.async_add_executor_job(
                partial(self._api.cloud.send, self._device.serial_number, data)
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_toggle_lock(self, data: dict | None = None) -> None:
        """Toggle device lock state."""
        set_lock = not bool(self._device.locked)
        self.log(LoggerType.SERVICE_CALL, "Setting locked state to %s", set_lock)
        try:
            await self.hass.async_add_executor_job(
                partial(self._api.cloud.set_lock, self._device.serial_number, set_lock)
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_edgecut(self, data: dict | None = None) -> None:
        """Start edgecut routine."""
        self.log(
            LoggerType.SERVICE_CALL,
            "Starting edge cut task",
        )
        try:
            await self.hass.async_add_executor_job(
                partial(self._api.cloud.ots, self._device.serial_number, True, 0)
            )
        except NoOneTimeScheduleError:
            self.log(
                LoggerType.SERVICE_CALL,
                "This device does not support Edge-Cut-OnDemand",
                log_level=LogLevel.ERROR,
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_toggle_partymode(self, data: dict | None = None) -> None:
        """Toggle partymode state."""
        if "party_mode_enabled" in data:
            set_partymode = bool(data["party_mode_enabled"])
        else:
            set_partymode = not bool(self._device.partymode_enabled)

        self.log(LoggerType.SERVICE_CALL, "Setting PartyMode to %s", set_partymode)
        try:
            await self.hass.async_add_executor_job(
                partial(
                    self._api.cloud.set_partymode,
                    self._device.serial_number,
                    set_partymode,
                )
            )
        except NoPartymodeError as ex:
            self.log(
                LoggerType.SERVICE_CALL, "%s", ex.args[0], log_level=LogLevel.ERROR
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_restart(self, data: dict | None = None):
        """Restart mower baseboard OS."""
        self.log(LoggerType.SERVICE_CALL, "Restarting")
        try:
            await self.hass.async_add_executor_job(
                self._api.cloud.restart, self._device.serial_number
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_ots(self, data: dict | None = None) -> None:
        """Begin OTS routine."""
        self.log(
            LoggerType.SERVICE_CALL,
            "Starting OTS with boundary set to %s and running for %s minutes",
            data[ATTR_BOUNDARY],
            data[ATTR_RUNTIME],
        )
        try:
            await self.hass.async_add_executor_job(
                partial(
                    self._api.cloud.ots,
                    self._device.serial_number,
                    data[ATTR_BOUNDARY],
                    data[ATTR_RUNTIME],
                )
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_send_raw(self, data: dict | None = None) -> None:
        """Send a raw command to the device."""
        self.log(LoggerType.SERVICE_CALL, "Data being sent: %s", data[ATTR_JSON])
        try:
            await self.hass.async_add_executor_job(
                partial(
                    self._api.cloud.send, self._device.serial_number, data[ATTR_JSON]
                )
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_config(self, data: dict | None = None) -> None:
        """Set config parameters."""
        tmpdata = {}
        try:
            if "multizone_distances" in data:
                self.log(
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
                    raise HomeAssistantError(
                        "Incorrect format for multizone distances array"
                    )

                tmpdata["mz"] = sections

            if "multizone_probabilities" in data:
                self.log(
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
                if sum(sections) not in [100, 0]:
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
                self.log(LoggerType.SERVICE_CALL, "New config: %s", data)
                await self.hass.async_add_executor_job(
                    partial(self._api.cloud.send, self._device.serial_number, data)
                )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc


class LandroidSelect(SelectEntity):
    """Representation of a Landroid select entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidSelectEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid select."""
        super().__init__()

        self.entity_description = description
        self.hass = hass

        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        _LOGGER.debug(
            "(%s, Setup) Added input_select '%s'",
            self._api.friendly_name,
            self._attr_name,
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})

        self._value = self.entity_description.value_fn(self._device) + 1
        self._attr_available = self._device.online
        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    async def handle_update(self) -> None:
        """Handle the updates when recieving an update signal."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if self._attr_available != self._device.online:
            self._attr_available = self._device.online

        try:
            self._value = self.entity_description.value_fn(self._device) + 1
        except AttributeError:
            return

        _LOGGER.debug(
            "(%s, Update signal) Updating select '%s' to '%s'",
            self._api.friendly_name,
            self._attr_name,
            self._value,
        )
        try:
            self.async_write_ha_state()
        except RuntimeError:
            contextlib.suppress(RuntimeError)

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return str(self._value)

    async def async_select_option(self, option: int) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "(%s, Set value) Setting selected value for '%s' to %s",
            self._api.friendly_name,
            self._attr_name,
            option,
        )
        try:
            self.entity_description.command_fn(self._api, str(int(option) - 1))
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc


class LandroidButton(ButtonEntity):
    """Representation of a Landroid button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidButtonEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid button."""
        super().__init__()

        self.entity_description = description
        self.hass = hass
        self._api = api
        self._config = config

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        self._attr_name = self.entity_description.name

        _LOGGER.debug(
            "(%s, Setup) Added button '%s'", self._api.friendly_name, self._attr_name
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})
        self._attr_extra_state_attributes = {}

        self._attr_available = self._device.online

        if self.entity_description.key == "request_update":
            self._available = True

        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    async def handle_update(self) -> None:
        """Handle updates."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if (
            self._attr_available != self._device.online
            and self.entity_description.key != "request_update"
        ):
            self._attr_available = self._device.online
        elif self.entity_description.key == "request_update":
            self._attr_available = self._available if self._device.online else False

        self.async_write_ha_state()

    def press(self) -> None:
        """Press the button."""
        try:
            self.entity_description.press_action(self._api, self._device.serial_number)
            if self.entity_description.key == "request_update":
                self._available = False
                self._attr_available = False
                self.hass.add_job(
                    async_call_later,
                    self.hass,
                    timedelta(minutes=15),
                    self._set_available,
                )

        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    def _set_available(self, *args, **kwargs) -> None:
        """Reenable button."""
        if self.entity_description.key == "request_update":
            self._available = True
            self._attr_available = self._available if self._device.online else False
            _LOGGER.debug(
                "(%s, Set available) Setting button '%s' availability to '%s'",
                self._api.friendly_name,
                self._attr_name,
                self._attr_available,
            )
            self.schedule_update_ha_state()


class LandroidSensor(SensorEntity):
    """Representation of a Landroid sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidSensorEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid sensor."""
        super().__init__()

        self.entity_description = description
        self.hass = hass
        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        _LOGGER.debug(
            "(%s, Setup) Added sensor '%s'", self._api.friendly_name, self._attr_name
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})
        self._attr_available = self._device.online
        self._attr_extra_state_attributes = {}

        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    async def async_added_to_hass(self) -> None:
        """Set state on adding to home assistant."""
        await self.handle_update()
        return await super().async_added_to_hass()

    async def handle_update(self) -> None:
        """Handle the updates when recieving an update signal."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if self._attr_available != self._device.online:
            self._attr_available = self._device.online

        old_val = self._attr_native_value
        old_attrib = self._attr_extra_state_attributes
        new_attrib = {}

        # try:
        new_val = self.entity_description.value_fn(self._device)
        # except AttributeError:
        #     new_val = None

        if old_val != new_val:
            self._attr_native_value = new_val

        self._attr_extra_state_attributes = {}

        if not isinstance(self.entity_description.attributes, type(None)):
            if self.entity_description.key == "battery_state":
                for key in self.entity_description.attributes:
                    new_attrib.update({key: self._device.battery[key]})
            elif self.entity_description.key == "error":
                for key in self.entity_description.attributes:
                    new_attrib.update({key: self._device.error[key]})
            elif self.entity_description.key == "next_start":
                self._attr_extra_state_attributes.update(self._device.schedules)
                self._attr_extra_state_attributes.pop("daily_progress")
                self._attr_extra_state_attributes.pop("next_schedule_start")
            elif self.entity_description.key == "distance":
                new_attrib.update({"meters": self._device.statistics["distance"]})
            elif self.entity_description.key == "worktime_total":
                (
                    new_attrib.update(
                        {"minutes": self._device.statistics["worktime_total"]}
                    )
                    if "worktime_total" in self._device.statistics
                    else None
                )
            elif self.entity_description.key == "blades_current_on":
                (
                    new_attrib.update({"minutes": self._device.blades["current_on"]})
                    if "current_on" in self._device.blades
                    else None
                )
            elif self.entity_description.key == "blades_total_on":
                (
                    new_attrib.update({"minutes": self._device.blades["total_on"]})
                    if "total_on" in self._device.blades
                    else None
                )
            elif self.entity_description.key == "reset_at":
                (
                    new_attrib.update({"minutes": self._device.blades["reset_at"]})
                    if "reset_at" in self._device.blades
                    else None
                )

        if old_attrib != new_attrib:
            self._attr_extra_state_attributes = new_attrib

        _LOGGER.debug(
            "(%s, Update signal) Updating sensor '%s' to new value '%s' with attributes '%s'",
            self._api.friendly_name,
            self._attr_name,
            self._attr_native_value,
            self._attr_extra_state_attributes,
        )

        try:
            self.async_write_ha_state()
        except RuntimeError:
            contextlib.suppress(RuntimeError)


class LandroidNumber(NumberEntity):
    """Representation of a Landroid number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidNumberEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid number entity."""
        super().__init__()

        self.entity_description = description
        self.hass = hass

        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        _LOGGER.debug(
            "(%s, Setup) Added switch '%s'",
            self._api.friendly_name,
            self._attr_name,
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})

        self._value = None  # self.entity_description.value_fn(self._api)
        self._attr_available = self._device.online
        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    @property
    def native_value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        return self._value

    async def async_added_to_hass(self) -> None:
        """Set state on adding to home assistant."""
        await self.handle_update()
        return await super().async_added_to_hass()

    async def handle_update(self) -> None:
        """Handle the updates when recieving an update signal."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if self._attr_available != self._device.online:
            self._attr_available = self._device.online

        try:
            self._value = self.entity_description.value_fn(self._api)
        except AttributeError:
            contextlib.suppress(AttributeError)

        _LOGGER.debug(
            "(%s, Update signal) Updating number '%s' to '%s'",
            self._api.friendly_name,
            self._attr_name,
            self._value,
        )
        try:
            self.async_write_ha_state()
        except RuntimeError:
            contextlib.suppress(RuntimeError)

    def set_native_value(self, value: float) -> None:
        """Set number value."""
        _LOGGER.debug(
            "(%s, Set value) Setting number value for '%s' to %s",
            self._api.friendly_name,
            self._attr_name,
            value,
        )

        try:
            self.entity_description.command_fn(self._api, value)
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc


class LandroidSwitch(SwitchEntity):
    """Representation of a Landroid switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidSwitchEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid switch."""
        super().__init__()

        self.entity_description = description
        self.hass = hass

        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        _LOGGER.debug(
            "(%s, Setup) Added switch '%s'",
            self._api.friendly_name,
            self._attr_name,
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})

        self._attr_extra_state_attributes = {}
        self._attr_available = self._device.online
        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    async def async_added_to_hass(self) -> None:
        """Set state on adding to home assistant."""
        await self.handle_update()
        return await super().async_added_to_hass()

    async def handle_update(self) -> None:
        """Handle the updates when recieving an update signal."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if self._attr_available != self._device.online:
            self._attr_available = self._device.online

        try:
            self._attr_is_on = self.entity_description.value_fn(self._device)
        except AttributeError:
            return

        _LOGGER.debug(
            "(%s, Update signal) Updating switch '%s' to '%s'",
            self._api.friendly_name,
            self._attr_name,
            self._attr_is_on,
        )
        try:
            self.async_write_ha_state()
        except RuntimeError:
            contextlib.suppress(RuntimeError)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.hass.async_add_executor_job(
                self.entity_description.command_fn,
                self._api.cloud,
                self._device.serial_number,
                True,
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.hass.async_add_executor_job(
                self.entity_description.command_fn,
                self._api.cloud,
                self._device.serial_number,
                False,
            )
        except NoConnectionError as exc:
            raise ConfigEntryNotReady() from exc

    @property
    def icon(self) -> str | None:
        """Return the icon specified."""
        if self.is_on and not isinstance(self.entity_description.icon_on, type(None)):
            return self.entity_description.icon_on
        elif not self.is_on and not isinstance(
            self.entity_description.icon_off, type(None)
        ):
            return self.entity_description.icon_off
        else:
            return super().icon


class LandroidBinarySensor(BinarySensorEntity):
    """Representation of a Landroid binary_sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        description: LandroidBinarySensorEntityDescription,
        api: LandroidAPI,
        config: ConfigEntry,
    ) -> None:
        """Initialize a Landroid binary_sensor."""
        super().__init__()

        self.entity_description = description
        self.hass = hass

        self._api = api
        self._config = config

        self._attr_name = self.entity_description.name

        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        _LOGGER.debug(
            "(%s, Setup) Added binary_sensor '%s'",
            self._api.friendly_name,
            self._attr_name,
        )

        self._attr_unique_id = util_slugify(
            f"{self._attr_name}_{self._config.entry_id}_{self._device.serial_number}"
        )
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.unique_id,
                    self._api.entry_id,
                    self._device.serial_number,
                )
            },
            "name": str(f"{self._api.friendly_name}"),
            "sw_version": self._device.firmware["version"],
            "manufacturer": self._api.config["type"].capitalize(),
            "model": self._device.model,
            "serial_number": self._device.serial_number,
        }

        if (
            not isinstance(self._device.mac_address, type(None))
            and self._device.mac_address != "__UUID__"
        ):
            _connections = {(dr.CONNECTION_NETWORK_MAC, self._device.mac_address)}
            self._attr_device_info.update({"connections": _connections})

        self._attr_extra_state_attributes = {}

        if self.entity_description.key == "online":
            self._attr_available = True
        else:
            self._attr_available = self._device.online

        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self._device.name}"),
            self.handle_update,
        )

    async def async_added_to_hass(self) -> None:
        """Set state on adding to home assistant."""
        await self.handle_update()
        return await super().async_added_to_hass()

    async def handle_update(self) -> None:
        """Handle the updates when recieving an update signal."""
        self._device: DeviceHandler = self._api.cloud.devices[self._api.device_name]

        if self._attr_available != self._device.online:
            if self.entity_description.key == "online":
                self._attr_available = True
            else:
                self._attr_available = self._device.online

        try:
            self._attr_is_on = self.entity_description.value_fn(self._device)
        except AttributeError:
            return

        _LOGGER.debug(
            "(%s, Update signal) Updating binary_sensor '%s' to '%s'",
            self._api.friendly_name,
            self._attr_name,
            self._attr_is_on,
        )
        try:
            self.async_write_ha_state()
        except RuntimeError:
            contextlib.suppress(RuntimeError)
