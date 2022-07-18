"""Data schemes used by Landroid Cloud integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_FRIDAY_BOUNDARY,
    ATTR_FRIDAY_END,
    ATTR_FRIDAY_START,
    ATTR_JSON,
    ATTR_MONDAY_BOUNDARY,
    ATTR_MONDAY_END,
    ATTR_MONDAY_START,
    ATTR_SATURDAY_BOUNDARY,
    ATTR_SATURDAY_END,
    ATTR_SATURDAY_START,
    ATTR_SUNDAY_BOUNDARY,
    ATTR_SUNDAY_END,
    ATTR_SUNDAY_START,
    ATTR_THURSDAY_BOUNDARY,
    ATTR_THURSDAY_END,
    ATTR_THURSDAY_START,
    ATTR_TORQUE,
    ATTR_TUESDAY_BOUNDARY,
    ATTR_TUESDAY_END,
    ATTR_TUESDAY_START,
    ATTR_TYPE,
    ATTR_WEDNESDAY_BOUNDARY,
    ATTR_WEDNESDAY_END,
    ATTR_WEDNESDAY_START,
    ATTR_ZONE,
    CLOUDS,
    DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(
            CONF_TYPE, default=[x for x in CLOUDS if x.lower() == "worx"][0]
        ): vol.In(CLOUDS),
    }
)

EMPTY_SCHEME = vol.All(cv.make_entity_service_schema({}))

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [DATA_SCHEMA],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SCHEDULE_SCHEME = vol.Schema(
    {
        vol.Required(ATTR_TYPE, default="primary"): vol.In(["primary", "secondary"]),
        vol.Optional(ATTR_MONDAY_START): str,
        vol.Optional(ATTR_MONDAY_END): str,
        vol.Optional(ATTR_MONDAY_BOUNDARY): bool,
        vol.Optional(ATTR_TUESDAY_START): str,
        vol.Optional(ATTR_TUESDAY_END): str,
        vol.Optional(ATTR_TUESDAY_BOUNDARY): bool,
        vol.Optional(ATTR_WEDNESDAY_START): str,
        vol.Optional(ATTR_WEDNESDAY_END): str,
        vol.Optional(ATTR_WEDNESDAY_BOUNDARY): bool,
        vol.Optional(ATTR_THURSDAY_START): str,
        vol.Optional(ATTR_THURSDAY_END): str,
        vol.Optional(ATTR_THURSDAY_BOUNDARY): bool,
        vol.Optional(ATTR_FRIDAY_START): str,
        vol.Optional(ATTR_FRIDAY_END): str,
        vol.Optional(ATTR_FRIDAY_BOUNDARY): bool,
        vol.Optional(ATTR_SATURDAY_START): str,
        vol.Optional(ATTR_SATURDAY_END): str,
        vol.Optional(ATTR_SATURDAY_BOUNDARY): bool,
        vol.Optional(ATTR_SUNDAY_START): str,
        vol.Optional(ATTR_SUNDAY_END): str,
        vol.Optional(ATTR_SUNDAY_BOUNDARY): bool,
    },
    extra=vol.ALLOW_EXTRA,
)

TORQUE_SCHEME = vol.Schema(
    {
        vol.Required(ATTR_TORQUE): vol.All(vol.Coerce(int), vol.Range(-50, 50)),
    },
    extra=vol.ALLOW_EXTRA,
)

SET_ZONE_SCHEME = vol.Schema(
    {vol.Required(ATTR_ZONE): vol.All(vol.Coerce(int), vol.Range(0, 3))},
    extra=vol.ALLOW_EXTRA,
)

RAW_SCHEME = vol.Schema(
    {
        vol.Required(ATTR_JSON): str,
    },
    extra=vol.ALLOW_EXTRA,
)


OTS_SCHEME = ""
