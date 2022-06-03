"""Utilities used for entity setup."""
# pylint: disable=relative-beyond-top-level
from __future__ import annotations
from typing import Any
import logging

from ..devices import Kress, LandXcape, Worx

_LOGGER = logging.getLogger(__name__)


def vendor_to_device(vendor: str):
    """Map vendor to device class."""
    device = None
    if vendor == "worx":
        device = Worx
    elif vendor == "kress":
        device = Kress
    elif vendor == "landxcape":
        device = LandXcape
    return device


