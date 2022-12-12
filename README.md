[![landroid_cloud](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic&label=Current%20release)](https://github.com/mtrab/landroid_cloud) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=plastic)](https://github.com/hacs/integration) ![Validate with hassfest](https://img.shields.io/github/workflow/status/mtrab/landroid_cloud/Code%20validation?label=Hass%20validation&style=plastic) ![Maintenance](https://img.shields.io/maintenance/yes/2022.svg?style=plastic&label=Integration%20maintained) [![downloads](https://img.shields.io/github/downloads/mtrab/landroid_cloud/total?style=plastic&label=Total%20downloads)](https://github.com/mtrab/landroid_cloud)<br />
[![Lokalize translation](https://img.shields.io/static/v1?label=Help%20translate&message=using%20Lokalize&color=green&style=plastic)](https://app.lokalise.com/public/97921736629219cb0306a3.84106577/) [![Buy me a coffee](https://img.shields.io/static/v1?label=Buy%20me%20a%20coffee&message=and%20say%20thanks&color=orange&logo=buymeacoffee&logoColor=white&style=plastic)](https://www.buymeacoffee.com/mtrab)


# INTEGRATION IS CURRENTLY NOT WORKING DUE TO API CHANGES
And because all the devices which I have access to are stored for the winter, I have no possibility to fix the integration until spring.
IF you want to use this integration AND have a mower that is still online and willing to lend me access to your account, please email me your account credentials on landroid_cloud(at)trab.dk

# Landroid Cloud

This component has been created to be used with Home Assistant.

Landroid Cloud presents a possibility to connect your Landroid Cloud compatible mowers to Home Assistant.<br />
Currently these vendors are supported:<br />
- Worx Landroid
- Kress
- LandXcape

### Installation:

#### HACS

- Ensure that HACS is installed.
- Search for and install the "Landroid Cloud" integration.
- Restart Home Assistant.
- Go to Integrations and add the Landroid Cloud integration

#### Manual installation

- Download the latest release.
- Unpack the release and copy the custom_components/landroid_cloud directory into the custom_components directory of your Home Assistant installation.
- Restart Home Assistant.
- Go to Integrations and add the Landroid Cloud integration

### Example entry for configuration.yaml (legacy)

```
landroid_cloud:
  - email: this@example.com
    password: YourPassword
```

You can add multiple accounts like in this example:

```
landroid_cloud:
  - email: this@example.com
    password: YourPassword
  - email: another@example.com
    password: AnotherPassword
```

If you have LandXcape or Kress robots you can add `type` to the config instead of default 'worx':

```
landroid_cloud:
  - email: this@example.com
    password: YourPassword
    type: landxcape
```

### Entities & Services

Once installed, the following entities are created in Home Assistant:

```
vacuum.[NAME_FROM_APP]
```

In addition, the following services are created:
Service name | Description
---|---
landroid_cloud.configure | Change configuration settings of device
landroid_cloud.partymode | Toggle PartyMode if supported by device
landroid_cloud.setzone | Set next zone to be mowed
landroid_cloud.lock | Toggle device lock
landroid_cloud.restart | Restart device baseboard OS
landroid_cloud.edgecut | Start edgecut routine if supported by device

You can simply add these to your Lovelace setup by adding an entity card or using [Barma-lej halandroid package](https://github.com/Barma-lej/halandroid)

### Translation

To handle submissions of translated strings I'm using [Lokalise](https://lokalise.com/).<br/>
They provide an amazing platform that is easy to use and maintain.<br/>
<br/>
To help out with the translation of this custom_component you need an account on Lokalise.<br/>
The easiest way to get one is to [click here](https://lokalise.com/login/) then select "Log in with GitHub".<br/>
<br/>
When you have created your account, [clich here](https://app.lokalise.com/public/97921736629219cb0306a3.84106577/) to join the project on Lokalise.<br/>
<br/>
Check Lokalise documentation [here](https://docs.lokalise.com/en/) - it's really good.<br/>
<br/>
Can't find the language you want to translate to? [Open a new language request](https://github.com/MTrab/landroid_cloud/issues/new?assignees=&labels=translation&template=translation_request.md&title=%5BLR%5D%3A+New%20language%20request)<br/>
<br/>
Contributions to the translations will be updated on every release of this component.


### Other useful information
#### Services and app stopped working

You might experience being banned from Worx Landroid Cloud service.
Follow this simple guide to make it work again:
* Go to [My Landroids](https://account.worxlandroid.com/product-items)
* Unlink your Landroid(s)
* Open app on mobile device
* Add Landroid(s)

### To-do

* Make this an official integration (far in the future as there is to many changes right now)
