# Release Notes Prep: v7 Breaking Changes

This note is intended as internal release-notes preparation for the v7 rewrite.

## Summary

The new integration is not a drop-in replacement for the legacy version.
The main breaking areas are:

- legacy services are no longer exposed
- new service names and payloads must be used for schedule management
- many entity keys changed
- several entities were removed
- legacy config entries now migrate forward automatically, but the stored data format changed
- many configuration and diagnostic entities are now disabled by default
- write-capable entities are unavailable while the mower is offline

## Breaking Changes

### Removed legacy services

The legacy integration exposed service calls that are not present in the new version:

- `landroid_cloud.config`
- `landroid_cloud.schedule`
- `landroid_cloud.send_raw`

Automations or scripts calling those services will break.

### New custom service model

The rewrite now exposes these custom services instead:

- `landroid_cloud.ots`
- `landroid_cloud.add_schedule`
- `landroid_cloud.edit_schedule`
- `landroid_cloud.delete_schedule`

This means old automations cannot be migrated by a simple rename.
Schedule-related automations must be rewritten to use the new service names and field structure.
Native device automations are available again for mower actions, conditions, and triggers, so the breaking change mainly affects automations that called the removed legacy services directly.

Key behavior differences:

- schedule creation now uses `days`, `start`, `duration`, and optional `boundary`
- schedule editing now targets an existing entry with `current_day` and optional `current_start`
- schedule deletion now uses `day` and optional `start`, or `all_schedules: true`
- the old generic schedule payload format is no longer used

### Mower state model changed

The mower entity still uses the v7 lawn mower platform, but detailed runtime states are exposed again where the cloud data supports them.

The current model includes detailed states such as:

- `idle`
- `starting`
- `edgecut`
- `zoning`
- `searching_zone`
- `escaped_digital_fence`

This reduces the migration gap versus legacy, but users should still verify any automation that depends on exact state names.

### Entity ID and unique ID churn

The new integration uses a different entity model and several entity keys have changed.
Because unique IDs are derived from `serial_number + entity_key`, Home Assistant will treat these as new entities.

Expected impact:

- dashboards will show missing entities
- automations and scripts targeting old entity IDs will break
- users may need to reassign entities manually in dashboards/helpers

### Config entry data changed

The stored config entry format changed in v7.
Older entries used the legacy `type` field and older unique ID patterns, while the new version stores a canonical `cloud` value and a new unique ID format.

Expected impact:

- existing v6 entries should now migrate automatically during setup
- manual delete-and-recreate should no longer be the normal upgrade path
- users with unusual or conflicting old unique IDs may still need manual cleanup if Home Assistant already has a collision

### Entity renames

Known high-impact renames:

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
- pause mode
- lock
- ACS
- rain sensor
- next schedule
- pitch
- roll
- yaw
- blade runtime at last reset
- blade runtime reset time
- most diagnostic sensors

### Next schedule behavior changed

`next_schedule` now becomes unavailable when the mower has no valid upcoming schedule.
Users coming from older behavior may previously have seen stale, misleading, or `unknown` values instead.

Expected impact:

- automations checking for a timestamp value should also handle `unavailable`
- dashboards may now show no upcoming schedule more explicitly

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

1. allow the integration to migrate the existing config entry before attempting manual cleanup
2. review broken or unavailable entities after upgrade
3. re-enable desired disabled-by-default entities manually
4. update automations/scripts to use the new entity IDs
5. remove or rewrite any automations using the removed legacy services
6. rewrite schedule automations to use the new `landroid_cloud.add_schedule`, `landroid_cloud.edit_schedule`, and `landroid_cloud.delete_schedule` services
7. update any automation using `next_schedule` so it handles `unavailable`

## Notes For Final Release Post

Recommended release-note sections:

- breaking changes
- removed services
- new schedule service model
- renamed entities
- disabled-by-default entities
- migration guidance
