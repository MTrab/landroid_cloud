[![landroid_cloud](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic&label=Current%20release)](https://github.com/mtrab/landroid_cloud) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=plastic)](https://github.com/hacs/integration) ![Maintenance](https://img.shields.io/maintenance/yes/2025.svg?style=plastic&label=Integration%20maintained) [![downloads](https://img.shields.io/github/downloads/mtrab/landroid_cloud/total?style=plastic&label=Total%20downloads)](https://github.com/mtrab/landroid_cloud)<br />
[![Lokalize translation](https://img.shields.io/static/v1?label=Help%20translate&message=using%20Lokalize&color=green&style=plastic)](https://app.lokalise.com/public/38508561643d2bcfb05550.72266746/) [![Buy me a coffee](https://img.shields.io/static/v1?label=Buy%20me%20a%20coffee&message=and%20say%20thanks&color=orange&logo=buymeacoffee&logoColor=white&style=plastic)](https://www.buymeacoffee.com/mtrab)

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

### Landroid Card

[Barma-lej](https://github.com/barma-lej) has created a custom card for the Landroid Cloud integration.<br/>
You can find installation instructions on [this Github repo](https://github.com/Barma-lej/landroid-card)

### Translation

To handle submissions of translated strings I'm using [Lokalise](https://lokalise.com/).<br/>
They provide an amazing platform that is easy to use and maintain.<br/>
<br/>
To help out with the translation of this custom_component you need an account on Lokalise.<br/>
The easiest way to get one is to [click here](https://lokalise.com/login/) then select "Log in with GitHub".<br/>
<br/>
When you have created your account, [clich here](https://app.lokalise.com/public/38508561643d2bcfb05550.72266746/) to join the project on Lokalise.<br/>
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
