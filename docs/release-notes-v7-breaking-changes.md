# Release Notes Prep: v7 Breaking Changes

This note is intended as internal release-notes preparation for the v7 rewrite.

## Summary

The new integration is not a drop-in replacement for the legacy version.
The main breaking areas are:

- legacy services are no longer exposed
- many entity keys changed
- several entities were removed
- many configuration and diagnostic entities are now disabled by default
- write-capable entities are unavailable while the mower is offline

## Breaking Changes

### Removed legacy services

The legacy integration exposed service calls that are not present in the new version:

- `landroid_cloud.config`
- `landroid_cloud.schedule`
- `landroid_cloud.send_raw`

Automations or scripts calling those services will break.

### Entity ID and unique ID churn

The new integration uses a different entity model and several entity keys have changed.
Because unique IDs are derived from `serial_number + entity_key`, Home Assistant will treat these as new entities.

Expected impact:

- dashboards will show missing entities
- automations and scripts targeting old entity IDs will break
- users may need to reassign entities manually in dashboards/helpers

### Entity renames

Known high-impact renames:

- `partymode` -> `party_mode`
- `locked` -> `lock`
- `offlimits` -> `off_limits`
- `offlimits_shortcut` -> `off_limits_shortcut`
- `zoneselect` -> `zone`
- `raindelay` -> `rain_delay`
- `timeextension` -> `time_extension`
- `battery_charging` -> `charging`
- `rainsensor_triggered` -> `rain_sensor`
- `battery_state` -> `battery`
- `next_start` -> `next_schedule`
- `battery_cycles_total` -> `battery_charge_cycles_total`
- `battery_cycles_current` -> `battery_charge_cycles_current`
- `blades_reset_at` -> `blade_runtime_reset_at`
- `blades_reset_time` -> `blade_runtime_reset_time`
- `distance` -> `distance_driven_total`
- `worktime_total` -> `mower_runtime_total`
- `edgecut` -> `edge_cut`
- `reset_charge_cycles` -> `reset_battery_cycles`

### Removed entities

The following legacy entities are not present in the current version:

- `online` binary sensor
- `request_update` button
- `restart` button
- `pitch` sensor
- `roll` sensor
- `yaw` sensor

### Disabled by default

Many configuration and diagnostic entities are now disabled by default.
This is intentional, but users may interpret it as missing functionality after upgrade.

Examples include:

- zone select
- last update
- rain delay
- cutting height
- time extension
- torque
- party mode
- lock
- rain sensor
- next schedule
- blade runtime at last reset
- blade runtime reset time
- most diagnostic sensors

### Availability changes

Write-capable entities are now unavailable while the mower is offline.
Read-only entities stay available so users can still inspect state and diagnostics.

This is safer behavior, but it changes how automations behave when devices are offline.

### RTK/Vision zone handling

RTK-style zones can now be read correctly, but write support is still not implemented for RTK zone selection.

Expected impact:

- users can see current/available RTK zones
- users cannot reliably change RTK zone from Home Assistant yet

## Migration Notes

Users upgrading from legacy should be told to:

1. review broken or unavailable entities after upgrade
2. re-enable desired disabled-by-default entities manually
3. update automations/scripts to use the new entity IDs
4. remove or rewrite any automations using the removed legacy services

## Notes For Final Release Post

Recommended release-note sections:

- breaking changes
- removed services
- renamed entities
- disabled-by-default entities
- migration guidance
