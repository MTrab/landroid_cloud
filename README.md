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
| Rain delay remaining | Standard | Disabled |
| Battery charge cycles total | Diagnostic | Disabled |
| Battery charge cycles since reset | Diagnostic | Disabled |
| Battery temperature | Diagnostic | Disabled |
| Battery voltage | Diagnostic | Disabled |
| Blade runtime total | Diagnostic | Disabled |
| Blade runtime since reset | Diagnostic | Disabled |
| Distance driven total | Diagnostic | Disabled |
| Mower runtime total | Diagnostic | Disabled |

Notes:

- `Next schedule` is exposed as a timestamp sensor and includes known schedule details as attributes.
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
| Party mode | Disabled | Requires party mode support |
| Lock | Disabled | |
| Off Limits | Enabled | Requires Off Limits support |
| Off Limits shortcuts | Enabled | Requires Off Limits support |
| ACS | Enabled | Requires ACS support |

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

#### Selects

| Entity | Category | Default | Notes |
| --- | --- | --- | --- |
| Zone | Configuration | Disabled | Requires mower to be online |

## Actions and control model

The integration does not add custom Home Assistant services. Control is exposed through native entities instead:

- Lawn mower actions for start, pause and dock
- Buttons for one-shot actions such as edge cut and counter resets
- Switches for boolean features such as ACS, lock and Off Limits
- Numbers for writable values such as rain delay, cutting height, time extension and torque
- Select for zone choice

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
