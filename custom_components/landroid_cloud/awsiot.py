"""Helpers for AWS IoT SDK behavior in async Home Assistant flows."""

from __future__ import annotations

import asyncio


def _prime_metrics_sync() -> None:
    """Initialize AWS IoT SDK metrics string outside the event loop.

    The first metrics build in awsiot performs importlib.metadata reads, which
    are blocking filesystem operations and must not run on Home Assistant's
    event loop thread.
    """
    try:
        from awsiot import mqtt_connection_builder
    except Exception:
        return

    try:
        if getattr(mqtt_connection_builder, "_metrics_str", None) is None:
            mqtt_connection_builder._get_metrics_str("")
    except Exception:
        return


async def async_prime_awsiot_metrics() -> None:
    """Prime AWS IoT SDK metrics cache in a worker thread."""
    await asyncio.to_thread(_prime_metrics_sync)
