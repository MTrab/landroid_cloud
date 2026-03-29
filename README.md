[![landroid_cloud](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic&label=Current%20release)](https://github.com/mtrab/landroid_cloud) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=plastic)](https://github.com/hacs/integration) [![downloads](https://img.shields.io/github/downloads/mtrab/landroid_cloud/total?style=plastic&label=Total%20downloads)](https://github.com/mtrab/landroid_cloud)

<a href="https://www.buymeacoffee.com/mtrab" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Landroid Cloud

This integration is designed for Home Assistant.

Landroid Cloud lets you connect your cloud-compatible mower to Home Assistant.

### Currently these vendors are supported:

- Worx Landroid
- Kress
- LandXcape

## Installation

### HACS

- Ensure that HACS is installed.
- Search for and install the `Landroid Cloud` integration (or click the blue button below to go there directly).
- Restart Home Assistant.
- Go to Integrations and add the Landroid Cloud integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MTrab&repository=landroid_cloud)

### Manual installation

- Download the latest release.
- Unpack the release and copy the custom_components/landroid_cloud directory into the custom_components directory of your Home Assistant installation.
- Restart Home Assistant.
- Go to Integrations and add the Landroid Cloud integration

## Setup

Open the integration setup directly:

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=landroid_cloud)

Or go to `Home Assistant` > `Settings` > `Devices & services`

Add the `Landroid Cloud` integration _(If it doesn't show, try CTRL+F5 to force a refresh of the page)_

Use the same credentials as in your mower app.

If you are upgrading from v6, existing config entries should now migrate into v7 automatically instead of requiring a full remove and re-add.

## Landroid Card

[Barma-lej](https://github.com/barma-lej) has created a custom card for the Landroid Cloud integration.<br/>
You can find installation instructions on [this Github repo](https://github.com/Barma-lej/landroid-card)


## Integration overview

The integration exposes each mower as a Home Assistant device with a native lawn mower entity and a set of related entities for telemetry, diagnostics and configuration.

Write-capable entities become unavailable while the mower is offline. Read-only entities remain available so status and diagnostics can still be inspected.

### Supported vendors

- Worx Landroid
- Kress
- LandXcape

### Exposed entities

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

- `Next schedule` is exposed as a timestamp sensor and includes known schedule details as attributes.
- `Auto schedule nutrition` exposes the configured N/P/K values when auto schedule provides them.
- `Auto schedule exclusion schedules` summarizes exclusion rules and exposes the normalized schedule details as attributes.
- `Rain delay remaining` is only available while a rain delay is active. When the mower reports `0` minutes remaining, the sensor is exposed as unavailable instead of reporting `0`.
- Duration and distance sensors suggest user-friendly display units where Home Assistant supports conversion.

#### Binary sensors

| Entity | Category | Default |
| --- | --- | --- |
| Charging | Diagnostic | Enabled |
| Rain sensor | Diagnostic | Disabled |

#### Switches

All switches are configuration entities and require the mower to be online.

| Entity | Default | Notes |
| --- | --- | --- |
| Auto schedule | Disabled | |
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

## Actions and control model

The integration exposes control through native entities and custom `landroid_cloud` services:

- Lawn mower actions for start, pause and dock
- Device automations for mower actions, triggers, and conditions in Home Assistant automations
- Buttons for one-shot actions such as edge cut and counter resets
- Switches for boolean features such as auto schedule, party mode, ACS, lock and Off Limits
- Numbers for writable values such as rain delay, cutting height, time extension, torque and lawn metadata
- Select entities for zone choice and auto-schedule tuning
- The `landroid_cloud.ots` service for starting a one-time schedule
- The `landroid_cloud.add_schedule`, `landroid_cloud.edit_schedule`, and `landroid_cloud.delete_schedule` services for schedule management
- Additional auto-schedule services for nutrition and exclusion schedule management

Supported device automation states include mowing, docked, returning, error, edge cut, starting, zoning, searching for zone, idle, rain delayed, and escaped digital fence.

### Auto-schedule refresh behavior

Auto-schedule settings are written through observed mower API calls, not through the MQTT push channel used for many runtime updates.

Because of that, changes made from Home Assistant do not appear immediately in the vendor app, and changes made in the vendor app do not appear immediately in Home Assistant. Updated values become visible after the next API refresh cycle.

### Zone handling

Legacy mowers expose the configured start-point zones for selection.
RTK/Vision style zone IDs are exposed read-only, and changing the selected RTK zone from Home Assistant is not supported yet.

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

Creates one or more recurring schedule entries in a single action call.

Fields:

- `days`: One or more days of the week
- `start`: Start time in `HH:MM` format
- `duration`: Duration in minutes
- `boundary`: Optional. If omitted, boundary defaults to `false` on mowers that require it

Behavior:

- If you select multiple days, the same schedule is created for each selected day
- On mowers with two slots per day, the integration automatically chooses the first or second free slot
- On mowers that support more than two daily entries, the integration will keep adding entries on the selected day as long as the mower accepts them

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
- When moving an entry to a different day, the integration automatically resolves the correct slot behind the scenes

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

### Finding the right schedule to edit or delete

Enable the `Next schedule` sensor if you want a simple view of the normalized schedule data the integration uses. Its attributes include `schedule_entries`, which can help you see which days and start times currently exist for the mower.

## Availability behavior

- Read-only entities stay available when the mower is offline
- Write-capable entities are marked unavailable when the mower is offline
- If coordinator data itself is unavailable, all related entities become unavailable

## Diagnostics and issue reporting

If you open an issue, include a Home Assistant diagnostics download whenever possible. Diagnostics are much more useful than pasted JSON fragments or screenshots of attributes.

## Other useful information
### Services and app stopped working

You might experience being banned from Worx Landroid Cloud service.
Follow this simple guide to make it work again:
* Go to [My Landroids](https://account.worxlandroid.com/product-items)
* Unlink your Landroid(s)
* Open app on mobile device
* Add Landroid(s)
