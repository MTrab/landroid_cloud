"""Runtime models for the Landroid Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from pyworxcloud import WorxCloud

from .coordinator import LandroidCloudCoordinator


@dataclass(slots=True)
class LandroidRuntimeData:
    """Runtime data stored on config entries."""

    cloud: WorxCloud
    coordinator: LandroidCloudCoordinator
