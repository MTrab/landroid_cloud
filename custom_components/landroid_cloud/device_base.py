"""Define device classes."""
# pylint: disable=unused-argument,too-many-instance-attributes,no-self-use
from __future__ import annotations
from functools import partial
import json
from typing import Any

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)

from homeassistant.components.vacuum import (
    ENTITY_ID_FORMAT,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)

from homeassistant.core import callback, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    entity_registry as er,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pyworxcloud import (
    NoPartymodeError,
    WorxCloud,
)
from pyworxcloud.states import ERROR_TO_DESCRIPTION

from .api import LandroidAPI

from .attribute_map import ATTR_MAP

from .const import (
    ATTR_BOUNDARY,
    ATTR_RUNTIME,
    ATTR_ZONE,
    BUTTONTYPE_TO_SERVICE,
    DOMAIN,
    LOGLEVEL,
    SCHEDULE_TO_DAY,
    SCHEDULE_TYPE_MAP,
    SERVICE_CONFIG,
    SERVICE_EDGECUT,
    SERVICE_LOCK,
    SERVICE_OTS,
    SERVICE_PARTYMODE,
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
    UPDATE_SIGNAL_REACHABILITY,
    UPDATE_SIGNAL_ZONES,
    LandroidFeatureSupport,
)

from .scheme import (
    SCHEDULE_SCHEME as SCHEME_SCHEDULE,
    SET_ZONE_SCHEME,
    TORQUE_SCHEME,
)

from .utils.schedules import pass_thru, parseday
from .utils.logger import LandroidLogger, LoggerType, LogLevel

LOGGER = LandroidLogger(__name__, LOGLEVEL)

# Commonly supported features
SUPPORT_LANDROID_BASE = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
)


class LandroidCloudBaseEntity:
    """
    Define a base Landroid Cloud entity class.\n
    \n
    Override these functions as needed by the specific device integration:\n
    async def async_edgecut(self, service_call: ServiceCall) -> None:\n
    async def async_toggle_lock(self, service_call: ServiceCall) -> None:\n
    async def async_toggle_partymode(self, service_call: ServiceCall) -> None:\n
    async def async_restart(self, service_call: ServiceCall) -> None:\n
    async def async_set_zone(self, service_call: ServiceCall) -> None:\n
    async def async_config(self, service_call: ServiceCall) -> None:\n
    async def async_ots(self, service_call: ServiceCall) -> None:\n
    async def async_set_schedule(self, service_call: ServiceCall) -> None:\n
    async def async_set_torque(self, service_call: ServiceCall) -> None:\n
    def zone_mapping(self) -> None:\n
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

        LOGGER.set_api(api)
        # self._check_features(base_features)

    def zone_mapping(self) -> None:
        """Map current zone correct."""
        return None

    # async def async_edgecut(self, service_call: ServiceCall, other) -> None:
    async def async_edgecut(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Called to start edge cut task."""
        return None

    async def async_toggle_lock(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Toggle lock state."""
        return None

    async def async_toggle_partymode(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Toggle partymode."""
        return None

    async def async_restart(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Restart baseboard OS."""
        return None

    async def async_set_zone(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set next zone."""
        return None

    async def async_config(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Configure device."""
        return None

    async def async_ots(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Start one-time-schedule."""
        return None

    async def async_set_schedule(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set cutting schedule."""
        return None

    async def async_set_torque(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set wheel torque."""
        return None

    @staticmethod
    def get_ots_scheme() -> Any:
        """Return device specific OTS_SCHEME."""
        return None

    @staticmethod
    def get_config_scheme() -> Any:
        """Return device specific CONFIG_SCHEME."""
        return None

    def register_services(self) -> None:
        """Register services."""
        LOGGER.write(
            LoggerType.SERVICE_REGISTER,
            "Registering services for %s with features %s",
            self.api.name,
            self.api.features,
        )
        if self.api.features & LandroidFeatureSupport.EDGECUT:
            if not self.hass.services.has_service(DOMAIN, SERVICE_EDGECUT):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_EDGECUT,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_EDGECUT, self.async_edgecut
                )
            self.api.services.append(SERVICE_EDGECUT)

        if self.api.features & LandroidFeatureSupport.LOCK:
            if not self.hass.services.has_service(DOMAIN, SERVICE_LOCK):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_LOCK,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_LOCK, self.async_toggle_lock
                )
            self.api.services.append(SERVICE_LOCK)

        if self.api.features & LandroidFeatureSupport.PARTYMODE:
            if not self.hass.services.has_service(DOMAIN, SERVICE_PARTYMODE):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_PARTYMODE,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_PARTYMODE, self.async_toggle_partymode
                )
            self.api.services.append(SERVICE_PARTYMODE)

        if self.api.features & LandroidFeatureSupport.SETZONE:
            if not self.hass.services.has_service(DOMAIN, SERVICE_SETZONE):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_SETZONE,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_SETZONE, self.async_set_zone, SET_ZONE_SCHEME
                )
            self.api.services.append(SERVICE_SETZONE)

        if self.api.features & LandroidFeatureSupport.RESTART:
            if not self.hass.services.has_service(DOMAIN, SERVICE_RESTART):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_RESTART,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_RESTART, self.async_restart
                )
            self.api.services.append(SERVICE_RESTART)

        if self.api.features & LandroidFeatureSupport.CONFIG:
            if not self.hass.services.has_service(DOMAIN, SERVICE_CONFIG):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_CONFIG,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_CONFIG, self.async_config, self.get_config_scheme
                )
            self.api.services.append(SERVICE_CONFIG)

        if self.api.features & LandroidFeatureSupport.OTS:
            if not self.hass.services.has_service(DOMAIN, SERVICE_OTS):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_OTS,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_OTS, self.async_ots, self.get_ots_scheme
                )
            self.api.services.append(SERVICE_OTS)

        if self.api.features & LandroidFeatureSupport.SCHEDULES:
            if not self.hass.services.has_service(DOMAIN, SERVICE_SCHEDULE):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_SCHEDULE,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_SCHEDULE, self.async_set_schedule, SCHEME_SCHEDULE
                )
            self.api.services.append(SERVICE_SCHEDULE)

        if self.api.features & LandroidFeatureSupport.TORQUE:
            if not self.hass.services.has_service(DOMAIN, SERVICE_TORQUE):
                LOGGER.write(
                    LoggerType.SERVICE_ADD,
                    "%s was not found - adding.",
                    SERVICE_TORQUE,
                )
                self.hass.services.async_register(
                    DOMAIN, SERVICE_TORQUE, self.async_set_torque, TORQUE_SCHEME
                )
            self.api.services.append(SERVICE_TORQUE)

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
            "sw_version": self.api.device.firmware_version,
            "manufacturer": self.api.config["type"].capitalize(),
            "model": self.api.device.model,
        }

    async def async_added_to_hass(self):
        """Connect update callbacks."""
        await self.api.async_refresh()

        if isinstance(self.api.device_id, type(None)):
            entity_reg: EntityRegistry = er.async_get(self.hass)
            entry = entity_reg.async_get(self.entity_id)
            self.api.device_id = entry.device_id

        async_dispatcher_connect(
            self.hass,
            f"{UPDATE_SIGNAL}_{self.api.device.name}",
            self.update_callback,
        )

        async_dispatcher_connect(
            self.hass,
            f"{UPDATE_SIGNAL_ZONES}_{self.api.device.name}",
            self.update_selected_zone,
        )

        async_dispatcher_connect(
            self.hass,
            f"{UPDATE_SIGNAL_REACHABILITY}_{self.api.device.name}",
            self.register_services,
        )

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

    def data_update(self):
        """Update the device."""
        LOGGER.write(LoggerType.DATA_UPDATE, "Updating")
        master: WorxCloud = self.api.device

        methods = ATTR_MAP["default"]
        data = {}
        self._icon = methods["icon"]
        for prop, attr in methods["state"].items():
            if hasattr(master, prop):
                prop_data = getattr(master, prop)
                if not isinstance(prop_data, type(None)):
                    data[attr] = prop_data
        data["error"] = ERROR_TO_DESCRIPTION[master.error or 0]
        data["capabilities"] = []

        # Populate capabilities attribute
        if master.ots_capable:
            data["capabilities"].append("One-Time-Schedule")
            data["capabilities"].append("Edge cut")
        if master.partymode_capable:
            data["capabilities"].append("Party Mode")
        if master.torque_capable:
            data["capabilities"].append("Motor Torque")

        data["device_id"] = self.api.device_id

        try:
            # Convert int to bool for charging state
            data["charging"] = bool(data["charging"])
        except KeyError:
            # Charging attribute not available, defaulting to False
            data["charging"] = False

        # Remove wheel_torque attribute if the device doesn't support this setting
        if not master.torque_capable and "wheel_torque" in data:
            data.pop("wheel_torque")

        self._attributes.update(data)

        LOGGER.write(LoggerType.DATA_UPDATE, "Online: %s", master.online)

        self._available = (
            master.online
            if master.error == 0
            else (not bool(isinstance(master.error, type(None))))
        )
        state = STATE_INITIALIZING

        if not master.online and master.error == 0:
            state = STATE_OFFLINE
        elif master.error is not None and master.error > 0:
            if master.error > 0 and master.error != 5:
                state = STATE_ERROR
            elif master.error == 5:
                state = STATE_RAINDELAY
        else:
            try:
                state = STATE_MAP[master.status]
            except KeyError:
                state = STATE_INITIALIZING

        if "zone_probability" in self._attributes:
            if len(self._attributes["zone_probability"]) == 10:
                self.zone_mapping()

        LOGGER.write(LoggerType.DATA_UPDATE, "State '%s'", state)
        LOGGER.write(LoggerType.DATA_UPDATE, "Attributes:\n%s", self._attributes)
        self._attr_state = state

        self._serialnumber = master.serial_number
        self._battery_level = master.battery_percent


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
            zones = self.api.device.zone
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

    @property
    def extra_state_attributes(self) -> str:
        """Return sensor attributes."""
        return self._attributes

    @property
    def device_class(self) -> str:
        """Return the ID of the capability, to identify the entity for translations."""
        return f"{DOMAIN}__state"

    # @property
    # def robot_unique_id(self) -> str:
    #     """Return the unique id."""
    #     return f"landroid_{self._serialnumber}"

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
        self.schedule_update_ha_state(True)

    async def async_start(self) -> None:
        """Start or resume the task."""
        device: WorxCloud = self.api.device
        LOGGER.write(LoggerType.SERVICE_CALL, "Starting")
        await self.hass.async_add_executor_job(device.start)

    async def async_pause(self) -> None:
        """Pause the mowing cycle."""
        device: WorxCloud = self.api.device
        LOGGER.write(LoggerType.SERVICE_CALL, "Pausing")
        await self.hass.async_add_executor_job(device.pause)

    async def async_start_pause(self) -> None:
        """Toggle the state of the mower."""
        LOGGER.write(LoggerType.SERVICE_CALL, "Toggeling state")
        if STATE_MOWING in self.state:
            await self.async_pause()
        else:
            await self.async_start()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the device to return to the dock."""
        if self.state not in [STATE_DOCKED, STATE_RETURNING]:
            device: WorxCloud = self.api.device
            LOGGER.write(LoggerType.SERVICE_CALL, "Going back to dock with blades off")
            await self.hass.async_add_executor_job(device.safehome)

    async def async_stop(self, **kwargs: Any) -> None:
        """Alias for return to base function."""
        await self.async_return_to_base()

    async def async_set_zone(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set next zone to cut."""
        device: WorxCloud = self.api.device
        zone = service_call.data["zone"]
        LOGGER.write(LoggerType.SERVICE_CALL, "Setting zone to %s", zone)
        await self.hass.async_add_executor_job(partial(device.setzone, str(zone)))

    async def async_set_schedule(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set or change the schedule."""
        device: WorxCloud = self.api.device
        schedule_type = service_call.data["type"]
        schedule = {}
        if schedule_type == "secondary":
            # We are handling a secondary schedule
            # Insert primary schedule in dataset befor generating secondary
            schedule[SCHEDULE_TYPE_MAP["primary"]] = pass_thru(
                device.schedules["primary"]
            )

        schedule[SCHEDULE_TYPE_MAP[schedule_type]] = []
        LOGGER.write(LoggerType.SERVICE_CALL, "Generating %s schedule", schedule_type)
        for day in SCHEDULE_TO_DAY.items():
            day = day[1]
            if day["start"] in service_call.data:
                # Found day in dataset, generating an update to the schedule
                if not day["end"] in service_call.data:
                    raise HomeAssistantError(
                        f"No end time specified for {day['clear']}"
                    )
                schedule[SCHEDULE_TYPE_MAP[schedule_type]].append(
                    parseday(day, service_call.data)
                )
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
        LOGGER.write(
            LoggerType.SERVICE_CALL, "New %s schedule, %s", schedule_type, data
        )
        await self.hass.async_add_executor_job(partial(device.send, data))

    async def async_toggle_lock(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Toggle device lock state."""
        device: WorxCloud = self.api.device
        set_lock = not bool(device.locked)
        LOGGER.write(LoggerType.SERVICE_CALL, "Setting locked state to %s", set_lock)
        await self.hass.async_add_executor_job(partial(device.lock, set_lock))

    async def async_edgecut(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Start edgecut routine."""
        LOGGER.write(None, entity)
        LOGGER.write(None, service_call)
        device: WorxCloud = self.api.device
        LOGGER.write(LoggerType.SERVICE_CALL, "Starting edge cut task")
        # try:
        #     await self.hass.async_add_executor_job(partial(device.ots, True, 0))
        # except NoOneTimeScheduleError as ex:
        #     LOGGER.write(LoggerType.SERVICE_CALL, "%s", ex.args[0], log_level=LogLevel.ERROR)

    async def async_toggle_partymode(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Toggle partymode state."""
        device: WorxCloud = self.api.device
        set_partymode = not bool(device.partymode_enabled)
        LOGGER.write(LoggerType.SERVICE_CALL, "Setting PartyMode to %s", set_partymode)
        try:
            await self.hass.async_add_executor_job(
                partial(device.toggle_partymode, set_partymode)
            )
        except NoPartymodeError as ex:
            LOGGER.write(
                LoggerType.SERVICE_CALL, "%s", ex.args[0], log_level=LogLevel.ERROR
            )

    async def async_restart(
        self, entity: Entity = None, service_call: ServiceCall = None
    ):
        """Restart mower baseboard OS."""
        device: WorxCloud = self.api.device
        LOGGER.write(LoggerType.SERVICE_CALL, "Restarting")
        await self.hass.async_add_executor_job(device.restart)

    async def async_ots(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Begin OTS routine."""
        device: WorxCloud = self.api.device
        data = service_call.data
        LOGGER.write(
            LoggerType.SERVICE_CALL,
            "Starting OTS with boundary set to %s and running for %s minutes",
            data[ATTR_BOUNDARY],
            data[ATTR_RUNTIME],
        )
        await self.hass.async_add_executor_job(
            partial(device.ots, data[ATTR_BOUNDARY], data[ATTR_RUNTIME])
        )

    async def async_config(
        self, entity: Entity = None, service_call: ServiceCall = None
    ) -> None:
        """Set config parameters."""
        tmpdata = {}
        device: WorxCloud = self.api.device
        data = service_call.data

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
                raise HomeAssistantError(
                    "Incorrect format for multizone distances array"
                )

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
            await self.hass.async_add_executor_job(partial(device.send, data))
