"""The Wyze HA integration."""

from __future__ import annotations

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.check_config import HomeAssistantConfig

from wyze_sdk import Client

from .const import _LOGGER, API_TIMEOUT, DOMAIN, PLATFORMS, CONF_CLIENT


async def async_setup(
    hass: HomeAssistant, config: HomeAssistantConfig, discovery_info=None
):
    """Set up Wyze HA from a config entry."""

    if DOMAIN not in config:
        _LOGGER.debug(
            "Nothing to import from configuration.yaml, loading from " "Integrations",
        )
        return True

    domainconfig = config.get(DOMAIN)

    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.debug("Found existing config entries")
        for entry in hass.config_entries.async_entries(DOMAIN):
            if (
                entry.data.get(CONF_EMAIL) == domainconfig[CONF_EMAIL]
                and entry.data.get(CONF_PASSWORD) == domainconfig[CONF_PASSWORD]
            ):
                _LOGGER.debug("Updating existing entry")
                hass.config_entries.async_update_entry(
                    entry,
                    data={
                        CONF_EMAIL: domainconfig[CONF_EMAIL],
                        CONF_PASSWORD: domainconfig[CONF_PASSWORD],
                    },
                )
                entry_found = True
                break
    if not entry_found:
        _LOGGER.debug("Creating new config entry")
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_EMAIL: domainconfig[CONF_EMAIL],
                    CONF_PASSWORD: domainconfig[CONF_PASSWORD],
                },
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Wyze Home Assistant Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    try:
        with async_timeout.timeout(API_TIMEOUT):

            _LOGGER.debug("Initialize connection to Ayla networks API")

            client = await hass.async_add_executor_job(
                Client,
                config_entry.data.get(CONF_EMAIL),
                config_entry.data.get(CONF_PASSWORD),
            )

            response = await hass.async_add_executor_job(client.api_test)

            if response is not None:
                _LOGGER.error("Authentication error connecting to Wyze: %s", response)
                return False

    except CannotConnect as exc:
        raise ConfigEntryNotReady from exc

    hass.data[DOMAIN][config_entry.entry_id] = {CONF_CLIENT: client}

    for platform in PLATFORMS:
        hass.create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
