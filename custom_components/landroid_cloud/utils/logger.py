"""Landroid Cloud integration wide logger component."""
# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import logging

from homeassistant.backports.enum import StrEnum

try:
    from ..api import LandroidAPI
except:  # pylint: disable=bare-except
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
    """Basic logger instance."""

    def __init__(
        self,
        name: str = None,
        api: LandroidAPI = None,
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        """Initialize base logger."""

        self.logapi = api
        self.logname = name
        self.loglevel = log_level
        self.logdevicename = None

        if self.logapi:
            if hasattr(self.logapi, "friendly_name"):
                self.logdevicename = self.logapi.friendly_name
            elif hasattr(self.logapi, "name"):
                self.logdevicename = self.logapi.name

    def log(
        self,
        log_type: LoggerType | None,
        message: str,
        *args,
        log_level: str | None = None,
        device: str | bool | None = False,
    ):
        """Write to logger component."""
        logger = logging.getLogger(self.logname)

        prefix = ""
        if not log_type in [LoggerType.NONE, None]:
            if not device and not isinstance(device, type(None)):
                prefix = (
                    "(" + log_type + ") "
                    if isinstance(self.logapi, type(None))
                    else "("
                    + (
                        self.logapi.friendly_name
                        if hasattr(self.logapi, "friendly_name")
                        else self.logapi.name
                    )
                    + ", "
                    + log_type
                    + ") "
                )
            else:
                prefix = (
                    "(" + log_type + ") "
                    if isinstance(device, type(None))
                    else "(" + device + ", " + log_type + ") "
                )

        log_string = prefix + str(message)
        level = self.loglevel if isinstance(log_level, type(None)) else log_level

        if level == "info":
            if args:
                logger.info(log_string, *args)
            else:
                logger.info(log_string)
        elif level == "warning":
            if args:
                logger.warning(log_string, *args)
            else:
                logger.warning(log_string)
        elif level == "critical":
            if args:
                logger.critical(log_string, *args)
            else:
                logger.critical(log_string)
        elif level == "error":
            if args:
                logger.error(log_string, *args)
            else:
                logger.error(log_string)
        elif level == "debug":
            logger.debug(log_string, *args)

    def log_set_api(self, api: LandroidAPI) -> None:
        """Set integration API."""
        self.logapi = api
        self.logdevicename = api.friendly_name

    def log_set_name(self, name: str) -> None:
        """Sets the namespace name used in logging."""
        self.logname = name
