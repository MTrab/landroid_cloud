"""Landroid Cloud integration wide logger component."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging

from homeassistant.backports.enum import StrEnum

try:
    from ..api import LandroidAPI
except:
    pass


class LoggerType(StrEnum):
    """Defines the available logger types."""

    NONE = "None"
    API = "API"
    GENERIC = "Generic"
    AUTHENTICATION = "Authentication"
    DATA_UPDATE = "Update signal"
    SETUP = "Setup"
    SETUP_IMPORT = "Setup, Import"
    CONFIG = "Config"
    CONFIG_IMPORT = "Config, Import"
    SERVICE = "Service"
    SERVICE_REGISTER = "Service Register"
    SERVICE_ADD = "Service Add"
    SERVICE_CALL = "Service Call"
    FEATURE = "Feature"
    FEATURE_ASSESSMENT = "Feature Assessment"
    BUTTON = "Button"
    SELECT = "Select"
    MOWER = "Mower"
    SENSOR = "Sensor"
    DEVELOP = "DEVELOPER INFO"


class LogLevel(StrEnum):
    """Define loglevels."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class LandroidLogger:
    """Define logger."""

    def __init__(
        self, name: str, log_level: LogLevel = LogLevel.DEBUG, api: LandroidAPI = None
    ):
        """Initialize logger."""
        self._api = api
        self._devicename: str | None = (
            None if isinstance(api, type(None)) else api.friendly_name
        )
        self._logname = name
        self._loglevel = log_level
        self._logger: logging.Logger = logging.getLogger(name)

        if not isinstance(self._devicename, type(None)):
            self._logger = self._logger.getChild(self._devicename)

    def set_child(self, name: str):
        """Set child logger."""
        self._logger = self._logger.getChild(name)

    def set_api(self, api: LandroidAPI):
        """Set integration API."""
        self._api = api
        self._devicename = api.friendly_name

    def write(
        self,
        log_type: LoggerType | None,
        message: str,
        *args,
        log_level: str | None = None,
    ):
        """Write to logger component."""
        prefix = ""
        if not log_type in [LoggerType.NONE, None]:
            prefix = (
                "(" + log_type + ") "
                if isinstance(self._devicename, type(None))
                else "(" + self._devicename + ", " + log_type + ") "
            )

        log_string = prefix + str(message)
        level = self._loglevel if isinstance(log_level, type(None)) else log_level

        if level == "info":
            if args:
                self._logger.info(log_string, *args)
            else:
                self._logger.info(log_string)
        elif level == "warning":
            if args:
                self._logger.warning(log_string, *args)
            else:
                self._logger.warning(log_string)
        elif level == "critical":
            if args:
                self._logger.critical(log_string, *args)
            else:
                self._logger.critical(log_string)
        elif level == "error":
            if args:
                self._logger.error(log_string, *args)
            else:
                self._logger.error(log_string)
        elif level == "debug":
            self._logger.debug(log_string, *args)
