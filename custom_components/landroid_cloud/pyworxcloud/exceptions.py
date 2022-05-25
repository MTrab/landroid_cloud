"""Exceptions definitions."""


class NoPartymodeError(Exception):
    """Define an error when partymode is not supported."""


class NoOneTimeScheduleError(Exception):
    """Define an error when OTS is not supported."""


class OfflineError(Exception):
    """Define an offline error."""
