"""Define device classes."""
# pylint: disable=unused-argument
from __future__ import annotations
from functools import partial
import json
import logging
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
    entity_platform,
)
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pyworxcloud import WorxCloud
from pyworxcloud.states import ERROR_TO_DESCRIPTION

from . import LandroidAPI

from .attribute_map import ATTR_MAP

from .const import (
    ATTR_ZONE,
    BUTTONTYPE_TO_SERVICE,
    DOMAIN,
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
    EMPTY_SCHEME,
    SCHEDULE_SCHEME as SCHEME_SCHEDULE,
    SET_ZONE_SCHEME,
    TORQUE_SCHEME,
)

from .utils.schedules import pass_thru, parseday

# Commonly supported features
SUPPORT_LANDROID_BASE = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
)


_LOGGER = logging.getLogger(__name__)


class LandroidCloudBaseEntity:
    """
    Define a base Landroid Cloud entity class.

    Override these async service functions as needed by the specific device integration:
    async def async_edgecut(self, service_call: ServiceCall) -> None:
    async def async_toggle_lock(self, service_call: ServiceCall) -> None:
    async def async_toggle_partymode(self, service_call: ServiceCall) -> None:
    async def async_restart(self, service_call: ServiceCall) -> None:
    async def async_setzone(self, service_call: ServiceCall) -> None:
    async def async_config(self, service_call: ServiceCall) -> None:
    async def async_ots(self, service_call: ServiceCall) -> None:
    async def async_set_schedule(self, service_call: ServiceCall) -> None:
    async_set_torque(self, service_call: ServiceCall) -> None:
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
        self._serialnumber = None
        self._icon = None
        self._name = f"{api.friendly_name}"
        self._mac = api.device.mac
        self._connections = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

    async def async_edgecut(self, service_call: ServiceCall) -> None:
        """Called to start edge cut task."""
        return None

    async def async_toggle_lock(self, service_call: ServiceCall) -> None:
        """Toggle lock state."""
        return None

    async def async_toggle_partymode(self, service_call: ServiceCall) -> None:
        """Toggle partymode."""
        return None

    async def async_restart(self, service_call: ServiceCall) -> None:
        """Restart baseboard OS."""
        return None

    async def async_setzone(self, service_call: ServiceCall) -> None:
        """Set next zone."""
        return None

    async def async_config(self, service_call: ServiceCall) -> None:
        """Configure device."""
        return None

    async def async_ots(self, service_call: ServiceCall) -> None:
        """Start one-time-schedule."""
        return None

    async def async_set_schedule(self, service_call: ServiceCall) -> None:
        """Set cutting schedule."""
        return None

    async def async_set_torque(self, service_call: ServiceCall) -> None:
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
        platform = entity_platform.async_get_current_platform()

        if self.features & LandroidFeatureSupport.EDGECUT:
            platform.async_register_entity_service(
                SERVICE_EDGECUT,
                EMPTY_SCHEME,
                self.async_edgecut,
            )
            self.api.services.append(SERVICE_EDGECUT)

        if self.features & LandroidFeatureSupport.LOCK:
            platform.async_register_entity_service(
                SERVICE_LOCK,
                EMPTY_SCHEME,
                self.async_toggle_lock,
            )
            self.api.services.append(SERVICE_LOCK)

        if self.features & LandroidFeatureSupport.PARTYMODE:
            platform.async_register_entity_service(
                SERVICE_PARTYMODE,
                EMPTY_SCHEME,
                self.async_toggle_partymode,
            )
            self.api.services.append(SERVICE_PARTYMODE)

        if self.features & LandroidFeatureSupport.SETZONE:
            platform.async_register_entity_service(
                SERVICE_SETZONE,
                SET_ZONE_SCHEME,
                self.async_setzone,
            )
            self.api.services.append(SERVICE_SETZONE)

        if self.features & LandroidFeatureSupport.RESTART:
            platform.async_register_entity_service(
                SERVICE_RESTART,
                EMPTY_SCHEME,
                self.async_restart,
            )
            self.api.services.append(SERVICE_RESTART)

        if self.features & LandroidFeatureSupport.CONFIG:
            _LOGGER.debug(self.get_config_scheme())
            platform.async_register_entity_service(
                SERVICE_CONFIG,
                self.get_config_scheme,
                self.async_config,
            )
            self.api.services.append(SERVICE_CONFIG)

        if self.features & LandroidFeatureSupport.OTS:
            platform.async_register_entity_service(
                SERVICE_OTS,
                self.get_ots_scheme,
                self.async_ots,
            )
            self.api.services.append(SERVICE_OTS)

        if self.features & LandroidFeatureSupport.SCHEDULES:
            platform.async_register_entity_service(
                SERVICE_SCHEDULE,
                SCHEME_SCHEDULE,
                self.async_set_schedule,
            )
            self.api.services.append(SERVICE_SCHEDULE)

        if self.features & LandroidFeatureSupport.TORQUE:
            platform.async_register_entity_service(
                SERVICE_TORQUE,
                TORQUE_SCHEME,
                self.async_set_torque,
            )
            self.api.services.append(SERVICE_TORQUE)

    @property
    def features(self) -> int:
        """Flag which Landroid specifics are supported."""
        return self._attr_landroid_features

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
            "model": self.api.device.board,
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

    def zone_mapping(self):
        """Map zones correct."""
        return False

    async def async_update(self):
        """Update the device."""
        _LOGGER.debug("Updating %s", self.entity_id)
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

        self._attributes.update(data)

        _LOGGER.debug("%s online: %s", self._name, master.online)
        self._available = master.online
        state = STATE_INITIALIZING

        if not master.online:
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

        _LOGGER.debug("%s state '%s'", self._name, state)
        _LOGGER.debug("\nAttributes:\n%s", self._attributes)
        # self._state = state
        self._attr_state = state

        self._serialnumber = master.serial
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

    # def __init__(self, hass, api):
    #     """Init new Landroid Cloud mower."""
    #     super().__init__(hass, api)
    #     self._attr_landroid_features = None

    @property
    def extra_state_attributes(self):
        """Return sensor attributes."""
        return self._attributes

    @property
    def device_class(self) -> str:
        """Return the ID of the capability, to identify the entity for translations."""
        return f"{DOMAIN}__state"

    @property
    def robot_unique_id(self):
        """Return the unique id."""
        return f"landroid_{self._serialnumber}"

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self._battery_level

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def state(self):
        """Return sensor state."""
        return self._attr_state

    @callback
    def update_callback(self):
        """Get new data and update state."""
        self.schedule_update_ha_state(True)

    async def async_start(self):
        """Start or resume the task."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Starting %s", self._name)
        await self.hass.async_add_executor_job(device.start)

    async def async_pause(self):
        """Pause the mowing cycle."""
        device: WorxCloud = self.api.device
        _LOGGER.debug("Pausing %s", self._name)
        await self.hass.async_add_executor_job(device.pause)

    async def async_start_pause(self):
        """Toggle the state of the mower."""
        _LOGGER.debug("Toggeling state of %s", self._name)
        if STATE_MOWING in self.state:
            await self.async_pause()
        else:
            await self.async_start()

    async def async_return_to_base(self, **kwargs: Any):
        """Set the vacuum cleaner to return to the dock."""
        if self.state not in [STATE_DOCKED, STATE_RETURNING]:
            device: WorxCloud = self.api.device
            _LOGGER.debug("Sending %s back to dock", self._name)
            await self.hass.async_add_executor_job(device.home)

    async def async_stop(self, **kwargs: Any):
        """Alias for return to base function."""
        await self.async_return_to_base()

    async def async_setzone(self, service_call: ServiceCall):
        """Set next zone to cut."""
        device: WorxCloud = self.api.device
        zone = service_call.data["zone"]
        _LOGGER.debug("Setting zone for %s to %s", self._name, zone)
        await self.hass.async_add_executor_job(partial(device.setzone, str(zone)))

    async def async_set_schedule(self, service_call: ServiceCall):
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
        _LOGGER.debug("Generating %s schedule", schedule_type)
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
        _LOGGER.debug(
            "New %s schedule, %s, sent to %s", schedule_type, data, self._name
        )
        await self.hass.async_add_executor_job(partial(device.send, data))
