"""Sensors for Heatzy."""
import logging

from heatzypy.exception import HeatzyException
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, PILOTEV1, PILOTEV2

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices = []
    for device in coordinator.data.values():
        product_key = device.get("product_key")
        if product_key in PILOTEV1:
            devices.append(LockSwitchEntity(coordinator, device["did"], "v1"))
        elif product_key in PILOTEV2:
            devices.append(LockSwitchEntity(coordinator, device["did"], "v2"))
    async_add_entities(devices, True)


class LockSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Lock Switch."""

    def __init__(self, coordinator, _unique_id, pilot_type):
        """Initialize switch."""
        self.coordinator = coordinator
        self._unique_id = _unique_id
        self._pilot_type = pilot_type

    @property
    def unique_id(self):
        """Return the unique id of this switch."""
        return f"lock_{self._unique_id}"

    @property
    def name(self):
        """Return the display name of this switch."""
        alias = self.coordinator.data[self._unique_id]["dev_alias"]
        return f"Lock switch {alias}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data[self._unique_id]["attr"].get("lock_switch", False)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        payload = {"raw": {"lock_switch": 1}}
        if self._pilot_type == "v2":
            payload = {"attrs": {"lock_switch": 1}}

        try:
            await self.hass.async_add_executor_job(
                self.coordinator.heatzy_client.control_device, self._unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)
        
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        payload = {"raw": {"lock_switch": 0}}
        if self._pilot_type == "v2":
            payload = {"attrs": {"lock_switch": 0}}

        try:
            await self.hass.async_add_executor_job(
                self.coordinator.heatzy_client.control_device, self._unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)
        
        await self.coordinator.async_request_refresh()
