[![landroid_cloud](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic&label=Current%20release)](https://github.com/mtrab/landroid_cloud) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=plastic)](https://github.com/hacs/integration) [![downloads](https://img.shields.io/github/downloads/mtrab/landroid_cloud/total?style=plastic&label=Total%20downloads)](https://github.com/mtrab/landroid_cloud)

<a href="https://www.buymeacoffee.com/mtrab" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Landroid Cloud

This is a Home Assistant integration for cloud-connected Landroid mowers.

### Supported vendors

- Worx Landroid
- Kress
- LandXcape

## Installation

### HACS

- Ensure that HACS is installed.
- Search for `Landroid Cloud` and install it, or use the button below.
- Restart Home Assistant.
- Go to Integrations and add `Landroid Cloud`.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MTrab&repository=landroid_cloud)

### Manual installation

- Download the latest release.
- Unpack it and copy `custom_components/landroid_cloud` into your Home Assistant `custom_components` directory.
- Restart Home Assistant.
- Go to Integrations and add `Landroid Cloud`.

## Setup

Open the integration setup directly:

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=landroid_cloud)

Or go to `Home Assistant` > `Settings` > `Devices & services`.

Add `Landroid Cloud`. If it doesn't show up, try `CTRL+F5` to refresh the page.

Use the same credentials as in your mower app.

If you're upgrading from v6, existing config entries should migrate to v7 automatically. You shouldn't need to remove and add the integration again.

## Landroid card

[Barma-lej](https://github.com/barma-lej) has created a custom card for the Landroid Cloud integration.<br/>
Installation instructions are in [the GitHub repository](https://github.com/Barma-lej/landroid-card).


## Integration overview

Each mower is added as a Home Assistant device. The integration creates a native lawn mower entity plus related entities for status, diagnostics, and configuration.

Entities that can change mower settings go unavailable while the mower is offline. Read-only entities stay available, so you can still see status and diagnostics.

### Supported vendors

- Worx Landroid
- Kress
- LandXcape

Fleet is not supported right now.
The Fleet API is still in early alpha, so this integration does not expose Fleet devices or controls.

### Known limitations

On Kress RTK Mission and Landroid Vision mowers, zones and schedules are read-only in this integration.
They can be read from the mower, but they cannot be changed from Home Assistant.

### Entities

#### Lawn mower

Each mower creates one lawn mower entity with these actions:

- Start mowing
- Pause
- Return to dock

#### Sensors

| Entity | Category | Default |
| --- | --- | --- |
| Battery | Standard | Enabled |
| Status | Standard | Enabled |
| Error | Diagnostic | Enabled |
| Signal strength | Diagnostic | Disabled |
| Daily progress | Standard | Disabled |
| Next schedule | Standard | Disabled |
| Auto schedule nutrition | Standard | Disabled |
| Auto schedule exclusion schedules | Standard | Disabled |
| Rain delay remaining | Standard | Disabled |
| Last update | Standard | Disabled |
| Battery charge cycles total | Diagnostic | Disabled |
| Battery charge cycles since reset | Diagnostic | Disabled |
| Battery temperature | Diagnostic | Disabled |
| Battery voltage | Diagnostic | Disabled |
| Pitch | Diagnostic | Disabled |
| Roll | Diagnostic | Disabled |
| Yaw | Diagnostic | Disabled |
| Blade runtime total | Diagnostic | Disabled |
| Blade runtime since reset | Diagnostic | Disabled |
| Blade runtime at last reset | Diagnostic | Disabled |
| Blade runtime reset time | Diagnostic | Disabled |
| Distance driven total | Diagnostic | Disabled |
| Mower runtime total | Diagnostic | Disabled |

Notes:

- `Next schedule` is a timestamp sensor and includes known schedule details as attributes.
- `Auto schedule nutrition` exposes the configured N/P/K values when auto schedule provides them.
- `Auto schedule exclusion schedules` summarizes exclusion rules and exposes the normalized schedule details as attributes.
- `Rain delay remaining` is only available while a rain delay is active. When the mower reports `0` minutes left, the sensor becomes unavailable instead of showing `0`.
- Duration and distance sensors suggest user-friendly display units where Home Assistant supports conversion.

#### Binary sensors

| Entity | Category | Default |
| --- | --- | --- |
| Charging | Diagnostic | Enabled |
| Rain sensor | Diagnostic | Disabled |

#### Updates

If the mower reports OTA firmware support, firmware updates are exposed through a native Home Assistant update entity.

| Entity | Category | Default | Notes |
| --- | --- | --- | --- |
| Firmware | Standard | Enabled | Requires OTA firmware support |

Notes:

- The update entity exposes the installed version, the latest available version, and release notes when the cloud API provides them.
- If the API provides a Markdown-friendly changelog, that version is used for release notes.
- Installing an update queues the latest available firmware from the vendor cloud. You can't pick an older version manually.

#### Switches

All switches are configuration entities and require the mower to be online.

| Entity | Default | Notes |
| --- | --- | --- |
| Auto schedule | Disabled | |
| Firmware auto update | Disabled | Requires OTA firmware support |
| Party mode | Disabled | Requires party mode support |
| Auto schedule irrigation | Disabled | Requires auto schedule to be enabled |
| Auto schedule exclude nights | Disabled | Requires auto schedule to be enabled |
| Lock | Disabled | |
| Off Limits | Enabled | Requires Off Limits support |
| Off Limits shortcuts | Enabled | Requires Off Limits support |
| ACS | Disabled | Requires ACS support |

#### Buttons

Buttons require the mower to be online.

| Entity | Category | Default | Notes |
| --- | --- | --- | --- |
| Edge cut | Standard | Disabled | Requires edge cut support |
| Reset blade runtime | Configuration | Disabled | |
| Reset battery cycles | Configuration | Disabled | |

#### Numbers

Numbers require the mower to be online and are disabled by default.

| Entity | Category | Range | Step | Notes |
| --- | --- | --- | --- | --- |
| Rain delay | Configuration | 0-300 min | 1 | |
| Cutting height | Configuration | 20-70 mm | 1 | Requires cutting height support |
| Time extension | Configuration | -100% to 100% | 10 | |
| Torque | Configuration | -50% to 50% | 1 | Requires torque support |
| Lawn size | Configuration | 0-100000 m² | 1 | |
| Lawn perimeter | Configuration | 0-100000 m | 1 | |

#### Selects

| Entity | Category | Default | Notes |
| --- | --- | --- | --- |
| Zone | Configuration | Disabled | Requires mower to be online |
| Auto schedule boost | Configuration | Disabled | Requires auto schedule to be enabled |
| Auto schedule grass type | Configuration | Disabled | Requires auto schedule to be enabled |
| Auto schedule soil type | Configuration | Disabled | Requires auto schedule to be enabled |

## Control and services

You can control the mower through native entities and custom `landroid_cloud` services:

- Lawn mower actions for start, pause, and dock
- Device automations for mower actions, triggers, and conditions
- Update entities for firmware version tracking, release notes, and OTA installs
- Buttons for one-shot actions such as edge cut and counter resets
- Switches for boolean features such as auto schedule, firmware auto update, party mode, ACS, lock, and Off Limits
- Numbers for writable values such as rain delay, cutting height, time extension, torque, and lawn metadata
- Select entities for zone choice and auto-schedule tuning
- The `landroid_cloud.ots` service for starting a one-time schedule
- The `landroid_cloud.add_schedule`, `landroid_cloud.edit_schedule`, and `landroid_cloud.delete_schedule` services for schedule management
- Additional auto-schedule services for nutrition and exclusion schedule management

Supported device automation states include mowing, docked, returning, error, edge cut, starting, zoning, searching for zone, idle, rain delayed, and escaped digital fence.

### Auto-schedule refresh behavior

Auto-schedule settings are written through observed mower API calls, not through the MQTT push channel used for many live updates.

That means changes made in Home Assistant do not show up right away in the vendor app, and changes made in the vendor app do not show up right away in Home Assistant. Updated values appear after the next API refresh.

On Kress RTK Mission and Landroid Vision mowers, schedules are read-only. The integration can show them, but it cannot create, edit, or delete them.

### Zone handling

Legacy mowers expose their configured start-point zones for selection.
RTK/Vision-style zone IDs are exposed as read-only. Changing the selected RTK zone from Home Assistant is not supported yet.

### Firmware updates

Firmware update metadata is read from the vendor cloud API and merged with the mower's live firmware payload when available.

Because availability and release notes come from cloud lookups instead of the usual push updates, Home Assistant may only show new firmware details after the next refresh or when the update entity refreshes its metadata.

### Custom integration services

All custom services target a `lawn_mower` entity from this integration.

#### `landroid_cloud.ots`

Starts a one-time mowing session on mowers that support it.

Fields:

- `boundary`: Include boundary or edge cutting
- `runtime`: Run time in minutes, from `10` to `120`

Example:

```yaml
action: landroid_cloud.ots
target:
  entity_id: lawn_mower.my_landroid
data:
  boundary: false
  runtime: 45
```

#### `landroid_cloud.add_schedule`

Creates one or more recurring schedule entries in a single action.

Fields:

- `days`: One or more days of the week
- `start`: Start time in `HH:MM` format
- `duration`: Duration in minutes
- `boundary`: Optional. If omitted, boundary defaults to `false` on mowers that require it

Behavior:

- If you select multiple days, the same schedule is created for each selected day
- On mowers with two slots per day, the integration picks the first or second free slot automatically
- On mowers that support more than two daily entries, the integration keeps adding entries on the selected day as long as the mower accepts them

Example:

```yaml
action: landroid_cloud.add_schedule
target:
  entity_id: lawn_mower.my_landroid
data:
  days:
    - monday
    - wednesday
    - friday
  start: "09:00"
  duration: 60
  boundary: false
```

#### `landroid_cloud.edit_schedule`

Updates one existing schedule entry.

Fields:

- `current_day`: The current day of the schedule you want to change
- `current_start`: Optional. Use this when that day has more than one schedule
- `day`: The new day
- `start`: The new start time in `HH:MM` format
- `duration`: The new duration in minutes
- `boundary`: Optional boundary setting for the updated entry

Behavior:

- If the selected current day only has one schedule, `current_start` is not needed
- If the day has multiple schedules, you must provide `current_start` so the integration knows which one to edit
- When moving an entry to a different day, the integration resolves the correct slot automatically

Example:

```yaml
action: landroid_cloud.edit_schedule
target:
  entity_id: lawn_mower.my_landroid
data:
  current_day: monday
  current_start: "09:00"
  day: tuesday
  start: "10:30"
  duration: 45
  boundary: true
```

#### `landroid_cloud.delete_schedule`

Deletes one schedule entry or clears the whole schedule.

Fields:

- `all_schedules`: Optional. Set to `true` to remove every schedule entry in one call
- `day`: Day of the schedule you want to delete
- `start`: Optional. Use this when the selected day has more than one schedule

Behavior:

- If `all_schedules` is `true`, all schedule entries are removed and `day` is not needed
- If a day only has one schedule, `start` is not needed
- If a day has multiple schedules, you must provide `start`

Examples:

```yaml
action: landroid_cloud.delete_schedule
target:
  entity_id: lawn_mower.my_landroid
data:
  day: monday
  start: "09:00"
```

```yaml
action: landroid_cloud.delete_schedule
target:
  entity_id: lawn_mower.my_landroid
data:
  all_schedules: true
```

### Finding the schedule you want to edit or delete

Enable the `Next schedule` sensor if you want an easy way to inspect the normalized schedule data used by the integration. Its attributes include `schedule_entries`, which can help you see which days and start times currently exist for the mower.

## Availability behavior

- Read-only entities stay available when the mower is offline
- Entities that can change mower settings are marked unavailable when the mower is offline
- If coordinator data is unavailable, all related entities become unavailable

## Diagnostics and issue reporting

If you open an issue, include a Home Assistant diagnostics download when possible. It is usually much more useful than pasted JSON fragments or screenshots of attributes.

## Other useful information

### Services and app stopped working

You may have been temporarily blocked by the Worx Landroid cloud service.
To restore access:

- Go to [My Landroids](https://account.worxlandroid.com/product-items)
- Unlink your Landroid(s)
- Open the mobile app
- Add the Landroid(s) again
