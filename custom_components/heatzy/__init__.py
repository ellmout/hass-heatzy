"""Heatzy platform configuration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
from heatzypy import HeatzyClient
from heatzypy.exception import HeatzyException, HttpRequestFailed
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .const import COMPONENTS, DEBOUNCE_COOLDOWN, DOMAIN

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass, config_entry):
    """Set up Heatzy as config entry."""
    hass.data[DOMAIN] = {}

    coordinator = HeatzyDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data is None:
        return False

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    for component in COMPONENTS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, component)
                for component in COMPONENTS
            ]
        )
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
        self.heatzy_client = HeatzyClient(
            config_entry.data[CONF_USERNAME], config_entry.data[CONF_PASSWORD]
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=DEBOUNCE_COOLDOWN, immediate=False
            ),
        )

    async def _async_update_data(self) -> dict:
        with async_timeout.timeout(30):
            try:
                devices = await self.hass.async_add_executor_job(
                    self.heatzy_client.get_devices
                )
                return {device["did"]: device for device in devices}
            except (HttpRequestFailed, HeatzyException) as error:
                raise UpdateFailed from error
