[![landroid_cloud](https://img.shields.io/github/release/mtrab/landroid_cloud/all.svg?style=plastic&label=Current%20release)](https://github.com/mtrab/landroid_cloud) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=plastic)](https://github.com/custom-components/hacs) ![Validate with hassfest](https://img.shields.io/github/workflow/status/mtrab/landroid_cloud/Code%20validation?label=Hass%20validation&style=plastic) ![Maintenance](https://img.shields.io/maintenance/yes/2022.svg?style=plastic&label=Integration%20maintained) [![downloads](https://img.shields.io/github/downloads/mtrab/landroid_cloud/total?style=plastic&label=Total%20downloads)](https://github.com/mtrab/landroid_cloud)<br />
[![Lokalize translation](https://img.shields.io/static/v1?label=Help%20translate&message=using%20Lokalize&color=green&style=plastic)](https://app.lokalise.com/public/97921736629219cb0306a3.84106577) [![Buy me a coffee](https://img.shields.io/static/v1?label=Buy%20me%20a%20coffee&message=and%20say%20thanks&color=orange&logo=buymeacoffee&logoColor=white&style=plastic)](https://www.buymeacoffee.com/mtrab)

{% if pending_update %}

## **New version is available**

{% endif %}{% if prerelease %}

## **NB!** This is a beta/pre-release version, use at your own risk!

{% endif %}

Custom component to add support for Landroid Cloud compatible mowers.
Currently these makes are supported:

*   Worx Landroid
*   Landxcape
*   Kress

In addition Aldi Ferrex are in a limited, experimental, support as well.

This component generates **1 lawn_mower entity** pr. available mower in an account.

## Configuration

Configuration is done through **Configuration > Integrations**

For full documentation, please see the [README](https://github.com/mtrab/landroid_cloud)