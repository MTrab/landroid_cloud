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
  email: your@email.ocm
  password: YourPassword
```

### Please note

Currently this integration is only supporting 1 mower pr. account. Unfortunately I don't have multiple myself, so having a hard time testing this.
