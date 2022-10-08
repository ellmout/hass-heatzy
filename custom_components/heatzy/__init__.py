"""Heatzy platform configuration."""
import logging
from datetime import timedelta

from heatzypy import HeatzyClient
from heatzypy.exception import HeatzyException, HttpRequestFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEBOUNCE_COOLDOWN, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = 60


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heatzy as config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = HeatzyDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    if coordinator.data is None:
        return False

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class HeatzyDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch datas."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
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
        session = async_create_clientsession(hass)
        self.heatzy_client = HeatzyClient(
            entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], session
        )

    async def _async_update_data(self) -> dict:
        """Update data."""
        try:
            devices = await self.heatzy_client.async_get_devices()
            return {device["did"]: device for device in devices}
        except (HttpRequestFailed, HeatzyException) as error:
            raise UpdateFailed(error) from error
