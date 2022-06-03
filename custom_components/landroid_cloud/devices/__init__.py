"""Device definitions."""
from __future__ import annotations

from .kress import KressButton, KressMowerDevice
from .landxcape import LandxcapeButton, LandxcapeMowerDevice
from .worx import (
    WorxButton,
    WorxMowerDevice,
    WorxSelect,
    WorxZoneSelect,
    CONFIG_SCHEME as WORX_CONFIG,
    OTS_SCHEME as WORX_OTS,
)

__all__ = []  # Init list

# Append Kress definitions
__all__.append("KressButton")
__all__.append("KressMowerDevice")

# Landxcape
__all__.append("LandxcapeButton")
__all__.append("LandxcapeMowerDevice")

# Worx
__all__.append("WorxButton")
__all__.append("WorxMowerDevice")
__all__.append("WorxSelect")
__all__.append("WorxZoneSelect")
__all__.append("WORX_CONFIG")
__all__.append("WORX_OTS")
