"""Heatzy platform configuration."""
import logging

from heatzypy import HeatzyClient
from heatzypy.exception import HeatzyException
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, HEATZY_DEVICES, HEATZY_API

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Load configuration for Heatzy component."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN not in config:
        return True

    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up Heatzy as config entry."""
    if config_entry.data is None:
        return False

    await async_connect_heatzy(hass, config_entry.data)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "climate")
    )
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_unload(config_entry, "climate")
    )
    return True


async def async_connect_heatzy(hass, data):
    """Connect to heatzy."""
    try:
        api = HeatzyClient(data[CONF_USERNAME], data[CONF_PASSWORD])
        devices = await hass.async_add_executor_job(api.get_devices)
        if devices is not None:
            hass.data[DOMAIN] = {HEATZY_API: api, HEATZY_DEVICES: devices}
    except HeatzyException as e:
        _LOGGER.error(f"Error: %s", e)
        raise HeatzyException(e)
