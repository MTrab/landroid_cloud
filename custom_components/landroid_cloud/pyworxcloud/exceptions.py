"""Exceptions definitions."""


class NoPartymodeError(Exception):
    """Define an error when partymode is not supported."""


class NoOneTimeScheduleError(Exception):
    """Define an error when OTS is not supported."""


class OfflineError(Exception):
    """Define an offline error."""


class TokenError(Exception):
    """Define an token error."""


class RequestException(Exception):
    """Define a request exception."""


class APIException(Exception):
    """Define an error when communicating with the API."""


class TimeoutException(Exception):
    """Define a timeout error."""
