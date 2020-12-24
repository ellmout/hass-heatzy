"""Config flow to configure Heatzy."""
import logging

from heatzypy.exception import HeatzyException

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from . import async_connect_heatzy
from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)

_LOGGER = logging.getLogger(__name__)


class HeatzyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Heatzy config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                await async_connect_heatzy(self.hass, user_input)
            except HeatzyException:
                errors["base"] = "cannot_connect"

            if "base" not in errors:
                return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
