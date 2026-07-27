"""Tests for the Landroid Cloud data coordinator."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pyworxcloud import LandroidEvent

from custom_components.landroid_cloud.binary_sensor import (
    BINARY_SENSORS,
    LandroidBinarySensor,
)
from custom_components.landroid_cloud.coordinator import LandroidCloudCoordinator


class _RecordingCloud:
    """Minimal WorxCloud stand-in that records callback registrations."""

    def __init__(self, mqtt_connected: bool | None = None) -> None:
        self.callbacks: dict = {}
        self.mqtt_connected = mqtt_connected

    def set_callback(self, event, func) -> None:
        self.callbacks[event] = func


class _ImmediateLoop:
    """Event loop stub that runs scheduled callbacks synchronously."""

    def __init__(self) -> None:
        self.scheduled: list = []

    def call_soon_threadsafe(self, callback, *args) -> None:
        self.scheduled.append((callback, args))
        callback(*args)


def _make_coordinator(cloud: _RecordingCloud) -> LandroidCloudCoordinator:
    coordinator = object.__new__(LandroidCloudCoordinator)
    coordinator.cloud = cloud
    coordinator.hass = SimpleNamespace(loop=_ImmediateLoop())
    coordinator.async_update_listeners = Mock()
    return coordinator


@pytest.mark.asyncio
async def test_async_setup_registers_mqtt_connection_callback() -> None:
    """Coordinator must subscribe to MQTT connection-state changes."""
    cloud = _RecordingCloud()
    coordinator = _make_coordinator(cloud)

    await coordinator.async_setup()

    assert LandroidEvent.MQTT_CONNECTION in cloud.callbacks
    assert LandroidEvent.DATA_RECEIVED in cloud.callbacks
    assert LandroidEvent.API in cloud.callbacks


@pytest.mark.asyncio
async def test_mqtt_connection_event_notifies_listeners_without_refetch() -> None:
    """A connection-state callback should refresh entities immediately."""
    cloud = _RecordingCloud(mqtt_connected=False)
    coordinator = _make_coordinator(cloud)
    await coordinator.async_setup()

    cloud.callbacks[LandroidEvent.MQTT_CONNECTION](state=False)

    coordinator.async_update_listeners.assert_called_once_with()
    # Scheduling must be thread-safe: pyworxcloud emits from the paho thread.
    assert coordinator.hass.loop.scheduled


@pytest.mark.asyncio
async def test_reconnect_updates_stale_connectivity_sensor() -> None:
    """Repro #1327: the connectivity sensor should track reconnect callbacks."""
    cloud = _RecordingCloud(mqtt_connected=False)
    coordinator = _make_coordinator(cloud)
    await coordinator.async_setup()

    entity = object.__new__(LandroidBinarySensor)
    entity.entity_description = next(
        description
        for description in BINARY_SENSORS
        if description.key == "mqtt_connected"
    )
    entity.coordinator = coordinator
    entity._serial_number = "serial"

    # Stale while MQTT is down.
    assert entity.is_on is False

    # pyworxcloud reconnects: the cloud property flips and the event fires.
    cloud.mqtt_connected = True
    cloud.callbacks[LandroidEvent.MQTT_CONNECTION](state=True)

    coordinator.async_update_listeners.assert_called_once_with()
    assert entity.is_on is True


@pytest.mark.asyncio
async def test_async_shutdown_resets_mqtt_connection_callback() -> None:
    """Shutdown should neutralize the MQTT connection callback."""
    cloud = _RecordingCloud()
    coordinator = _make_coordinator(cloud)
    await coordinator.async_setup()
    setup_handler = cloud.callbacks[LandroidEvent.MQTT_CONNECTION]

    await coordinator.async_shutdown()

    handler = cloud.callbacks[LandroidEvent.MQTT_CONNECTION]
    assert handler is not setup_handler
    # The reset handler must be a harmless no-op that tolerates kwargs.
    assert handler(state=True) is None
    coordinator.async_update_listeners.assert_not_called()


def test_schedule_connection_update_survives_loop_shutdown() -> None:
    """Scheduling after loop shutdown should be swallowed, not raised."""
    cloud = _RecordingCloud()
    coordinator = object.__new__(LandroidCloudCoordinator)
    coordinator.cloud = cloud
    coordinator.async_update_listeners = Mock()

    class _DeadLoop:
        def call_soon_threadsafe(self, *_args) -> None:
            raise RuntimeError("Event loop is closed")

    coordinator.hass = SimpleNamespace(loop=_DeadLoop())

    coordinator._schedule_connection_update()

    coordinator.async_update_listeners.assert_not_called()
