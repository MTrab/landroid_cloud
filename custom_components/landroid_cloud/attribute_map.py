"""Attribute map used by Landroid Cloud integration."""

from __future__ import annotations

from homeassistant.const import ATTR_LOCKED

from .const import ATTR_ACCESSORIES, ATTR_LAWN, ATTR_PARTYMODE, ATTR_TORQUE, ATTR_ZONE

ATTR_MAP = {
    "accessories": ATTR_ACCESSORIES,
    "lawn": ATTR_LAWN,
    "locked": ATTR_LOCKED,
    "partymode_enabled": ATTR_PARTYMODE,
    "torque": ATTR_TORQUE,
    "zone": ATTR_ZONE,
}
