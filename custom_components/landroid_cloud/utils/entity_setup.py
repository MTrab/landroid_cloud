"""Utilities used for entity setup."""
# pylint: disable=relative-beyond-top-level
from __future__ import annotations

from ..device_base import LandroidCloudMowerBase
from ..devices import Kress, LandXcape, Worx


def vendor_to_device(vendor: str):
    """Map vendor to device class."""
    device: LandroidCloudMowerBase = None
    if vendor == "worx":
        device = Worx
    elif vendor == "kress":
        device = Kress
    elif vendor == "landxcape":
        device = LandXcape
    return device
