"""Heatzy platform configuration."""
import logging
from datetime import timedelta

from heatzypy import HeatzyClient
from heatzypy.exception import HeatzyException, HttpRequestFailed
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEBOUNCE_COOLDOWN, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = 60


async def async_setup_entry(hass, config_entry):
    """Set up Heatzy as config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = HeatzyDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data is None:
        return False

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return True


class HeatzyDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch datas."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
    ) -> None:
        """Class to manage fetching Heatzy data API."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=DEBOUNCE_COOLDOWN, immediate=False
            ),
        )        
        self.heatzy_client = HeatzyClient(
            config_entry.data[CONF_USERNAME], config_entry.data[CONF_PASSWORD]
        )


    async def _async_update_data(self) -> dict:
        """Update data."""
        try:
            devices = await self.heatzy_client.async_get_devices()
            return {device["did"]: device for device in devices}
        except (HttpRequestFailed, HeatzyException) as error:
            raise UpdateFailed(error) from error
