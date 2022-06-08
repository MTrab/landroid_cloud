"""LandXcape device definition."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.vacuum import StateVacuumEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import dispatcher_send

from pyworxcloud import (
    NoOneTimeScheduleError,
    NoPartymodeError,
    WorxCloud,
)

from .. import LandroidAPI

from ..const import LandroidFeatureSupport

from ..device_base import (
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
    SUPPORT_LANDROID_BASE,
)


_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = SUPPORT_LANDROID_BASE

DEVICE_FEATURES = (
    LandroidFeatureSupport.MOWER
    | LandroidFeatureSupport.BUTTON
    | LandroidFeatureSupport.CONFIG
    | LandroidFeatureSupport.RESTART
)


class Button(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Landxcape button."""

    def __init__(
        self,
        description: ButtonEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ) -> None:
        """Initialize a Landxcape button."""
        super().__init__(description, hass, api, DEVICE_FEATURES)


class MowerDevice(LandroidCloudMowerBase, StateVacuumEntity):
    """Definition of Landxcape device."""

    def __init__(self, hass: HomeAssistant, api: LandroidAPI):
        """Initialize a Landxcape mower device."""
        super().__init__(hass, api, DEVICE_FEATURES)

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES
