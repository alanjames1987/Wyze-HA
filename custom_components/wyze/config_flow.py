"""Config flow for Wyze integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.exceptions import HomeAssistantError

from wyze_sdk import Client

from .const import _LOGGER, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data):

    """Validate the user input allows us to connect."""
    client = Client(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
    )

    response = await hass.async_add_executor_job(client.api_test)
    if response is not None:
        return False

    # Return info that you want to store in the config entry.
    return {"email": data[CONF_EMAIL], "password": data[CONF_PASSWORD]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wyze HA."""

    VERSION = 1

    async def async_step_user(self, user_input):
        """Handle the initial step."""
        errors = {}

        # if the data is being submitted log the user in
        if user_input is not None:
            return self.async_create_entry(title="Wyze HA", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
