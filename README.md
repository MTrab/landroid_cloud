[![](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic)](https://github.com/mtrab/landroid_cloud/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=plastic)](https://github.com/custom-components/hacs)

<a href="https://www.buymeacoffee.com/mtrab" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Landroid Cloud

This component has been created to be used with Home Assistant.

Landroid Cloud presents a possibility to connect your Landroid Cloud compatible mowers to Home Assistant.<br />
Currently these vendors are supported:<br />
- Worx Landroid
- Kress
- LandXcape

## Credit

Credit for inspiring to this component goes to [virtualzone](https://github.com/virtualzone) and [Eisha DeskApp](https://drive.google.com/drive/folders/0B63Mhn1k_KcbdXB5ZjdUUHNCWWc?resourcekey=0-DGwWcHl_QU2d_0clj8Xm3A&usp=sharing).

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

* Make this an official integration