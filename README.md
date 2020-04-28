[![](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic)](https://github.com/mtrab/landroid_cloud/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=plastic)](https://github.com/custom-components/hacs)

# Landroid Cloud

This component has been created to be used with Home Assistant.

Landroid Cloud presents a possibility to connect your cloud connected Worx Landroid mowers to Home Assistant.

### Credit

Credit for inspiring to this component goes to [virtualzone](https://github.com/virtualzone).

### Installation:

#### HACS

- Ensure that HACS is installed.
- Search for and install the "Landroid Cloud" integration.
- Restart Home Assistant.

#### Manual installation

- Download the latest release.
- Unpack the release and copy the custom_components/landroid_cloud directory into the custom_components directory of your Home Assistant installation.
- Restart Home Assistant.

### Example entry for configuration.yaml

```
landroid_cloud:
  - email: your@email.ocm
    password: YourPassword
```

You can add multiple accounts like in this example:

```
landroid_cloud:
  - email: your@email.ocm
    password: YourPassword
  - email: another@email.ocm
    password: AnotherPassword
```

### Entities & Services

Once installed, the following entities are created in Home Assistant:

```
sensor.landroid_[NAME_FROM_APP]_battery
sensor.landroid_[NAME_FROM_APP]_error
sensor.landroid_[NAME_FROM_APP]_status
```

In addition, the following services are created:

```
landroid_cloud.start
landroid_cloud.stop
landroid_cloud.pause
```

You can simply add these to your Lovelace setup by adding an entity card. A recommended Lovelace layout is being considered for a future release.

### Known bugs

If upgrading from version lower than 1.4, please comment out the landroid_cloud section from configuration.yaml, restart Home Assistant, reinsert the landroid_cloud section and restart again.
