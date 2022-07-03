"""Define device classes."""
# pylint: disable=unused-argument,too-many-instance-attributes,no-self-use
from __future__ import annotations
import asyncio

import json
from datetime import timedelta
from functools import partial
from pprint import pprint
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.vacuum import (
    ENTITY_ID_FORMAT,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.event import async_call_later
from homeassistant.util import slugify as util_slugify
from pyworxcloud import WorxCloud
from pyworxcloud.exceptions import (
    MQTTException,
    NoOneTimeScheduleError,
    NoPartymodeError,
    RateLimit,
)
from pyworxcloud.utils import Capability, DeviceCapability
from pyworxcloud.utils.capability import CAPABILITY_TO_TEXT

from .api import LandroidAPI
from .attribute_map import ATTR_MAP
from .const import (
    ATTR_BOUNDARY,
    ATTR_CAPABILITIES,
    ATTR_DEVICEIDS,
    ATTR_LANDROIDFEATURES,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MQTTCONNECTED,
    ATTR_RUNTIME,
    ATTR_SERVICE,
    ATTR_TORQUE,
    ATTR_ZONE,
    BUTTONTYPE_TO_SERVICE,
    DOMAIN,
    PLATFORMS_SECONDARY,
    SCHEDULE_TO_DAY,
    SCHEDULE_TYPE_MAP,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_OTS,
    SERVICE_PARTYMODE,
    SERVICE_REFRESH,
    SERVICE_RESTART,
    SERVICE_SCHEDULE,
    SERVICE_SETZONE,
    SERVICE_TORQUE,
    STATE_INITIALIZING,
    STATE_MAP,
    STATE_MOWING,
    STATE_OFFLINE,
    STATE_RAINDELAY,
    UPDATE_SIGNAL,
    LandroidFeatureSupport,
)
from .utils.logger import LandroidLogger, LoggerType, LogLevel
from .utils.schedules import parseday, pass_thru

# Commonly supported features
SUPPORT_LANDROID_BASE = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
)


class LandroidCloudBaseEntity(LandroidLogger):
    """
    Define a base Landroid Cloud entity class.\n
    \n
    Override these functions as needed by the specific device integration:\n
    async def async_edgecut(self,  data: dict|None = None) -> None:\n
    async def async_toggle_lock(self,  data: dict|None = None) -> None:\n
    async def async_toggle_partymode(self,  data: dict|None = None) -> None:\n
    async def async_restart(self,  data: dict|None = None) -> None:\n
    async def async_set_zone(self,  data: dict|None = None) -> None:\n
    async def async_config(self,  data: dict|None = None) -> None:\n
    async def async_ots(self,  data: dict|None = None) -> None:\n
    async def async_set_schedule(self,  data: dict|None = None) -> None:\n
    async def async_set_torque(self,  data: dict|None = None) -> None:\n
    """

    _battery_level: int | None = None
    _attr_state = STATE_INITIALIZING
    _attr_landroid_features: int | None = None

    def __init__(self, hass: HomeAssistant, api: LandroidAPI):
        """Init new base for a Landroid Cloud entity."""
        self.api = api
        self.hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name}")

        self._attributes = {}
        self._available = False
        self._unique_id = f"{api.device.serial_number}_{api.name}"
        self._serialnumber = api.device.serial_number
        self._icon = None
        self._name = f"{api.friendly_name}"
        self._mac = api.device.mac_address
        self._connections = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        super().__init__()

    @property
    def base_features(self) -> int:
        """Called to get the base features."""
        return None

    async def async_edgecut(self, data: dict | None = None) -> None:
        """Called to start edge cut task."""
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

    async def async_refresh(self, data: dict | None = None) -> None:
        """Refresh data from API endpoint."""
        try:
            self.api.device.refresh()
        except RateLimit as exc:
            self.log(LoggerType.SERVICE_CALL, exc.message, log_level=LogLevel.WARNING)
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
        """Return device info"""
        return {
            "connections": self._connections,
            "identifiers": {
                (
                    DOMAIN,
                    self.api.unique_id,
                    self.api.entry_id,
                    self.api.device.serial_number,
                )
            },
            "name": str(self._name),
            "sw_version": self.api.device.firmware["version"],
            "manufacturer": self.api.config["type"].capitalize(),
            "model": self.api.device.model,
        }

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        self.update_callback()

        if isinstance(self.api.device_id, type(None)):
            entity_reg: EntityRegistry = er.async_get(self.hass)
            entry = entity_reg.async_get(self.entity_id)
            self.api.device_id = entry.device_id
            if (
                not self.hass.data[DOMAIN][self.api.entry_id][ATTR_DEVICEIDS][
                    self.api.device.name
                ]
                == entry.device_id
            ):
                self.hass.data[DOMAIN][self.api.entry_id][ATTR_DEVICEIDS].update(
                    {self.api.device.name: entry.device_id}
                )

        self.log(
            LoggerType.SETUP,
            "Connecting to dispatcher signal '%s'",
            util_slugify(f"{UPDATE_SIGNAL}_{self.api.device.name}"),
        )
        async_dispatcher_connect(
            self.hass,
            util_slugify(f"{UPDATE_SIGNAL}_{self.api.device.name}"),
            self.update_callback,
        )

        # async_dispatcher_connect(
        #     self.hass,
        #     util_slugify(f"{UPDATE_SIGNAL_ZONES}_{self.api.device.name}"),
        #     self.update_selected_zone,
        # )

    @callback
    def update_callback(self):
        """Base update callback function"""
        return False

    @callback
    def update_selected_zone(self):
        """Update zone selections in select entity"""
        return False

    async def async_update(self):
        """Default async_update"""
        return

    @callback
    def register_services(self) -> None:
        """Register services."""
        self.log_set_name(__name__)
        self.log_set_api(self.api)
        if self.api.features == 0:
            self.log(
                LoggerType.SERVICE_REGISTER,
                "No services registred as feature flags is set to %s",
                self.api.features,
            )
            return

        self.log(
            LoggerType.SERVICE_REGISTER,
            "Registering services with feature flags set to %s",
            self.api.features,
        )

        if self.api.features & LandroidFeatureSupport.EDGECUT:
            self.api.services[SERVICE_EDGECUT] = {
                ATTR_SERVICE: self.async_edgecut,
            }

        if self.api.features & LandroidFeatureSupport.LOCK:
            self.api.services[SERVICE_LOCK] = {
                ATTR_SERVICE: self.async_toggle_lock,
            }

        if self.api.features & LandroidFeatureSupport.PARTYMODE:
            self.api.services[SERVICE_PARTYMODE] = {
                ATTR_SERVICE: self.async_toggle_partymode,
            }

        if self.api.features & LandroidFeatureSupport.SETZONE:
            self.api.services[SERVICE_SETZONE] = {
                ATTR_SERVICE: self.async_set_zone,
            }

        if self.api.features & LandroidFeatureSupport.REFRESH:
            self.api.services[SERVICE_REFRESH] = {
                ATTR_SERVICE: self.async_refresh,
            }

        if self.api.features & LandroidFeatureSupport.RESTART:
            self.api.services[SERVICE_RESTART] = {
                ATTR_SERVICE: self.async_restart,
            }

        if self.api.features & LandroidFeatureSupport.CONFIG:
            self.api.services[SERVICE_CONFIG] = {
                ATTR_SERVICE: self.async_config,
            }

        if self.api.features & LandroidFeatureSupport.OTS:
            self.api.services[SERVICE_OTS] = {
                ATTR_SERVICE: self.async_ots,
            }

        if self.api.features & LandroidFeatureSupport.SCHEDULES:
            self.api.services[SERVICE_SCHEDULE] = {
                ATTR_SERVICE: self.async_set_schedule,
            }

        if self.api.features & LandroidFeatureSupport.TORQUE:
            self.api.services[SERVICE_TORQUE] = {
                ATTR_SERVICE: self.async_set_torque,
            }

    def data_update(self):
        """Update the device."""
        self.log_set_name(__name__)
        self.log_set_api(self.api)
        self.log(LoggerType.DATA_UPDATE, "Updating")

        # self.api.check_features(self.base_features)
        device: WorxCloud = self.api.device

        data = {}

        for key, value in ATTR_MAP.items():
            if hasattr(device, key):
                data[value] = getattr(device, key)

        # Populate capabilities attribute
        data[ATTR_CAPABILITIES] = []
        capabilities: Capability = device.capabilities
        for capability in DeviceCapability:
            if capabilities.check(capability):
                data[ATTR_CAPABILITIES].append(CAPABILITY_TO_TEXT[capability])

        # If no extra capabilities were found,
        # then set the attribute to None (just for visual appearance)
        if len(data[ATTR_CAPABILITIES]) == 0:
            data.update({ATTR_CAPABILITIES: None})

        # Remove wheel_torque attribute if the device doesn't support this setting
        if not capabilities.check(DeviceCapability.TORQUE) and ATTR_TORQUE in data:
            data.pop(ATTR_TORQUE)

        data[ATTR_MQTTCONNECTED] = (
            device.mqtt.connected if hasattr(device, "mqtt") else False
        )

        data[ATTR_LANDROIDFEATURES] = self.api.features

        if hasattr(data, "gps"):
            data.update(
                {
                    ATTR_LATITUDE: data.gps["latitude"],
                    ATTR_LONGITUDE: data.gps["longitude"],
                }
            )

        self._attributes.update(data)

        self._available = (
            device.online
            if device.error.id in [-1, 0]
            else (not bool(isinstance(device.error.id, type(None))))
        )
        state = STATE_INITIALIZING

        if not device.online and device.error.id in [-1, 0]:
            state = STATE_OFFLINE
        elif device.error.id is not None and device.error.id > 0:
            if device.error.id > 0 and device.error.id != 5:
                state = STATE_ERROR
            elif device.error.id == 5:
                state = STATE_RAINDELAY
        else:
            try:
                state = STATE_MAP[device.status.id]
            except KeyError:
                state = STATE_INITIALIZING

        self.log(LoggerType.DATA_UPDATE, "Online: %s", device.online)
        self.log(LoggerType.DATA_UPDATE, "State '%s'", state)
        self.log(LoggerType.DATA_UPDATE, "Attributes:\n%s", self._attributes)
        self._attr_state = state

        self._serialnumber = device.serial_number
        if "percent" in device.battery:
            self._battery_level = device.battery["percent"]

        mqtt = device.mqtt.connected if hasattr(device, "mqtt") else False
        if not mqtt:
            # If MQTT is not connected, then pull state from API
            self.log(
                LoggerType.DATA_UPDATE,
                "MQTT connection is offline, scheduling Web API refresh in 15 minutes. "
                "Device is in readonly mode!",
                log_level=LogLevel.WARNING,
            )
            async_call_later(
                self.hass,
                timedelta(minutes=15),
                partial(self.async_get_state_from_api),
            )

    @callback
    async def async_get_state_from_api(self, dt=None) -> None:  # type: ignore pylint: disable=unused-argument,invalid-name
        """Fallback to fetching state from WebAPI rather than MQTT."""
        self.log(LoggerType.DATA_UPDATE, "Starting forced Web API refresh.")

        self.hass.async_add_executor_job(self.api.device.update)
        dispatcher_send(
            self.hass, util_slugify(f"{UPDATE_SIGNAL}_{self.api.device.name}")
        )


class LandroidCloudSelectEntity(LandroidCloudBaseEntity, SelectEntity):
    """Define a select entity."""

    def __init__(
        self,
        description: SelectEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ):
        """Initialize a new Landroid Cloud select entity."""
        super().__init__(hass, api)
        self.entity_description = description
        self._attr_unique_id = f"{api.name}_select_{description.key}"
        self._attr_options = []
        self._attr_current_option = None
        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name} {description.key}")

    @property
    def device_class(self) -> str:
        """Return the ID of the capability, to identify the entity for translations."""
        return f"{DOMAIN}__select_{self.entity_description.key}"


class LandroidCloudSelectZoneEntity(LandroidCloudSelectEntity):
    """Select zone entity definition."""

    @callback
    def update_selected_zone(self):
        """Get new data and update state."""
        if not isinstance(self._attr_options, type(None)):
            if len(self._attr_options) > 1:
                self._update_zone()

            try:
                self._attr_current_option = str(self.api.shared_options["current_zone"])
            except:  # pylint: disable=bare-except
                self._attr_current_option = None

        self.schedule_update_ha_state(True)

    def _update_zone(self) -> None:
        """Update zone selector options."""
        try:
            zones = self.api.device.zone["starting_point"]
        except:  # pylint: disable=bare-except
            zones = []

        if len(zones) == 4:
            options = []
            options.append("0")
            for idx in range(1, 4):
                if zones[idx] != 0:
                    options.append(str(idx))

            self._attr_options = options

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self._update_zone()
        self.update_selected_zone()

    async def async_select_option(self, option: str) -> None:
        """Set next zone to be mowed."""
        data = {ATTR_ZONE: int(option)}
        target = {"device_id": self.api.device_id}
        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_SETZONE,
            service_data=data,
            target=target,
        )


class LandroidCloudButtonBase(LandroidCloudBaseEntity, ButtonEntity):
    """Define a Landroid Cloud button class."""

    def __init__(
        self,
        description: ButtonEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ) -> None:
        """Init a new Landroid Cloud button."""
        super().__init__(hass, api)
        self.entity_description = description
        self._attr_unique_id = f"{api.name}_button_{description.key}"
        self.entity_id = ENTITY_ID_FORMAT.format(f"{api.name} {description.key}")

    @property
    def device_class(self) -> str:
        """Return the ID of the capability, to identify the entity for translations."""
        return f"{DOMAIN}__button_{self.entity_description.key}"

    async def async_press(
        self, **kwargs: Any  # pylint: disable=unused-argument
    ) -> None:
        """Press the button."""
        target = {"device_id": self.api.device_id}
        await self.hass.services.async_call(
            DOMAIN,
            BUTTONTYPE_TO_SERVICE[self.entity_description.key],
            target=target,
        )


class LandroidCloudMowerBase(LandroidCloudBaseEntity, StateVacuumEntity):
    """Define a base Landroid Cloud mower class."""

    _battery_level: int | None = None
    _attr_state = STATE_INITIALIZING

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        logger = LandroidLogger(name=__name__, api=self.api, log_level=LogLevel.DEBUG)
        logger.log(
            LoggerType.SETUP,
            "Features not assessed, calling assessment with base features at %s",
            self.base_features,
        )

        while not self.api.device.capabilities.ready:
            pass

        self.api.check_features(int(self.base_features))
        self.api.features_loaded = True
        while not self.api.features_loaded:
            self.log(
                LoggerType.FEATURE_ASSESSMENT,
                "Waiting for features to be fully loaded, before continuing",
            )

        self.register_services()

        self.hass.config_entries.async_setup_platforms(self.api.entry, PLATFORMS_SECONDARY)

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
        """Return the battery level of the vacuum cleaner."""
        return self._battery_level

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

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
        self.api.features_loaded = True
        self.schedule_update_ha_state(True)

    async def async_start(self) -> None:
        """Start or resume the task."""
        device: WorxCloud = self.api.device
        self.log(LoggerType.SERVICE_CALL, "Starting")
        try:
            await self.hass.async_add_executor_job(device.start)
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_pause(self) -> None:
        """Pause the mowing cycle."""
        device: WorxCloud = self.api.device
        self.log(LoggerType.SERVICE_CALL, "Pausing")
        try:
            await self.hass.async_add_executor_job(device.pause)
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_start_pause(self) -> None:
        """Toggle the state of the mower."""
        self.log(LoggerType.SERVICE_CALL, "Toggeling state")
        try:
            if STATE_MOWING in self.state:
                await self.async_pause()
            else:
                await self.async_start()
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the device to return to the dock."""
        if self.state not in [STATE_DOCKED, STATE_RETURNING]:
            device: WorxCloud = self.api.device
            self.log(LoggerType.SERVICE_CALL, "Going back to dock")
            try:
                # Try calling safehome
                await self.hass.async_add_executor_job(device.safehome)
                # Ensure we are going home, in case the safehome wasn't successful
                await self.hass.async_add_executor_job(device.home)
            except MQTTException:
                self.log(
                    LoggerType.SERVICE_CALL,
                    "Couldn't send command, MQTT was not connected",
                    log_level=LogLevel.ERROR,
                )
            except RateLimit as exc:
                self.log(
                    LoggerType.SERVICE_CALL,
                    exc.message,
                    log_level=LogLevel.WARNING,
                )

    async def async_stop(self, **kwargs: Any) -> None:
        """Alias for return to base function."""
        try:
            await self.async_return_to_base()
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_set_zone(self, data: dict | None = None) -> None:
        """Set next zone to cut."""
        device: WorxCloud = self.api.device
        zone = data["zone"]
        self.log(LoggerType.SERVICE_CALL, "Setting zone to %s", zone)
        try:
            await self.hass.async_add_executor_job(partial(device.setzone, str(zone)))
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_set_schedule(self, data: dict | None = None) -> None:
        """Set or change the schedule."""
        device: WorxCloud = self.api.device
        schedule_type = data["type"]
        schedule = {}
        if schedule_type == "secondary":
            # We are handling a secondary schedule
            # Insert primary schedule in dataset befor generating secondary
            schedule[SCHEDULE_TYPE_MAP["primary"]] = pass_thru(
                device.schedules["primary"]
            )

        schedule[SCHEDULE_TYPE_MAP[schedule_type]] = []
        self.log(LoggerType.SERVICE_CALL, "Generating %s schedule", schedule_type)
        for day in SCHEDULE_TO_DAY.items():
            day = day[1]
            if day["start"] in data:
                # Found day in dataset, generating an update to the schedule
                if not day["end"] in data:
                    raise HomeAssistantError(
                        f"No end time specified for {day['clear']}"
                    )
                schedule[SCHEDULE_TYPE_MAP[schedule_type]].append(parseday(day, data))
            else:
                # Didn't find day in dataset, parsing existing thru
                current = []
                current.append(device.schedules[schedule_type][day["clear"]]["start"])
                current.append(
                    device.schedules[schedule_type][day["clear"]]["duration"]
                )
                current.append(
                    int(device.schedules[schedule_type][day["clear"]]["boundary"])
                )
                schedule[SCHEDULE_TYPE_MAP[schedule_type]].append(current)

        if schedule_type == "primary":
            # We are generating a primary schedule
            # To keep a secondary schedule we need to pass this thru to the dataset
            schedule[SCHEDULE_TYPE_MAP["secondary"]] = pass_thru(
                device.schedules["secondary"]
            )

        data = json.dumps({"sc": schedule})
        self.log(LoggerType.SERVICE_CALL, "New %s schedule, %s", schedule_type, data)
        try:
            await self.hass.async_add_executor_job(partial(device.send, data))
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_toggle_lock(self, data: dict | None = None) -> None:
        """Toggle device lock state."""
        device: WorxCloud = self.api.device
        set_lock = not bool(device.locked)
        self.log(LoggerType.SERVICE_CALL, "Setting locked state to %s", set_lock)
        try:
            await self.hass.async_add_executor_job(partial(device.lock, set_lock))
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_edgecut(self, data: dict | None = None) -> None:
        """Start edgecut routine."""
        device: WorxCloud = self.api.device
        self.log(
            LoggerType.SERVICE_CALL,
            "Starting edge cut task",
        )
        try:
            await self.hass.async_add_executor_job(partial(device.ots, True, 0))
        except NoOneTimeScheduleError:
            self.log(
                LoggerType.SERVICE_CALL,
                "This device does not support Edge-Cut-OnDemand",
                log_level=LogLevel.ERROR,
            )
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_toggle_partymode(self, data: dict | None = None) -> None:
        """Toggle partymode state."""
        device: WorxCloud = self.api.device
        set_partymode = not bool(device.partymode_enabled)
        self.log(LoggerType.SERVICE_CALL, "Setting PartyMode to %s", set_partymode)
        try:
            await self.hass.async_add_executor_job(
                partial(device.toggle_partymode, set_partymode)
            )
        except NoPartymodeError as ex:
            self.log(
                LoggerType.SERVICE_CALL, "%s", ex.args[0], log_level=LogLevel.ERROR
            )
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_restart(self, data: dict | None = None):
        """Restart mower baseboard OS."""
        device: WorxCloud = self.api.device
        self.log(LoggerType.SERVICE_CALL, "Restarting")
        try:
            await self.hass.async_add_executor_job(device.restart)
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_ots(self, data: dict | None = None) -> None:
        """Begin OTS routine."""
        device: WorxCloud = self.api.device
        self.log(
            LoggerType.SERVICE_CALL,
            "Starting OTS with boundary set to %s and running for %s minutes",
            data[ATTR_BOUNDARY],
            data[ATTR_RUNTIME],
        )
        try:
            await self.hass.async_add_executor_job(
                partial(device.ots, data[ATTR_BOUNDARY], data[ATTR_RUNTIME])
            )
        except MQTTException:
            self.log(
                LoggerType.SERVICE_CALL,
                "Couldn't send command, MQTT was not connected",
                log_level=LogLevel.ERROR,
            )
        except RateLimit as exc:
            self.log(
                LoggerType.SERVICE_CALL,
                exc.message,
                log_level=LogLevel.WARNING,
            )

    async def async_config(self, data: dict | None = None) -> None:
        """Set config parameters."""
        tmpdata = {}
        device: WorxCloud = self.api.device

        if "raindelay" in data:
            self.log(
                LoggerType.SERVICE_CALL,
                "Setting raindelayto %s minutes",
                data["raindelay"],
            )
            tmpdata["rd"] = int(data["raindelay"])

        if "timeextension" in data:
            self.log(
                LoggerType.SERVICE_CALL,
                "Setting timeextension to %s%%",
                data["timeextension"],
            )
            tmpdata["sc"] = {}
            tmpdata["sc"]["p"] = int(data["timeextension"])

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
            self.log(LoggerType.SERVICE_CALL, "New config: %s", data)
            try:
                await self.hass.async_add_executor_job(partial(device.send, data))
            except MQTTException:
                self.log(
                    LoggerType.SERVICE_CALL,
                    "Couldn't send command, MQTT was not connected",
                    log_level=LogLevel.ERROR,
                )
            except RateLimit as exc:
                self.log(
                    LoggerType.SERVICE_CALL,
                    exc.message,
                    log_level=LogLevel.WARNING,
                )
