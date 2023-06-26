<p align="center">
    <img src="https://raw.githubusercontent.com/alanjames1987/Wyze-HA/master/.attachments/hero.png">
</p>

<h1 align="center">

[Wyze Custom Integration](https://github.com/alanjames1987/Wyze-HA) for Home Assistant

</h1>

# About

This is a custom integration to allow control and viewing of the Wyze robot vacuum from within Home Assistant.

This integration is based on [Wyze-SDK](https://github.com/shauntarves/wyze-sdk) from [@shauntarves](https://github.com/shauntarves) and since this SDK is not official the integration can break whenever Wyze makes changes to their API.

# Installation

## HACS

1. It's recommended to install this custom component using [HACS](https://hacs.xyz/).

1. To install HACS please see their installation instructions.

**The following information may change in future versions of HACS so it's always best to refer to the official HACS documentation [here](https://hacs.xyz/docs/faq/custom_repositories/).**

1. Once HACS is installed navigate to the HACS interface and click on "Integrations".

1. From "Integrations" click on the three dots in the top right corner and click "Custom reponsitories".

1. Paste in the GitHub link to this repository, [https://github.com/alanjames1987/Wyze-HA](https://github.com/alanjames1987/Wyze-HA) and select "Integration" as the category.

1. Click add and the integration will be added to HACS.

1. You should now see the integration in your HACS integations list. Click on it and click "Download" in the bottom corner. Select a version and click "Download".

1. This may take some time but once it's complete restart Home Assistant.

## Configure

1. Once Home Assistant restarts navigate to the Home Assistant Devices & Services page by clicking the gear icon in the bottom left of your Home Assistant interface and then clicking "Devices & Services".

1. Once there click the "Add Integration" button in the bottom right corner and search for "Wyze".

1. Click it and the integration will install and start the configuration process.

1. You will need to have your Wyze login credentials available and will need to have 2FA disabled on your Wyze account.

1. Enter your credentials and the integration will start it's sync with Wyze.

