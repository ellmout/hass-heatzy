"""Sensors for Heatzy."""
import logging

from heatzypy.exception import HeatzyException
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices = []
    for device in coordinator.data.values():
        devices.append(LockSwitchEntity(coordinator, device["did"]))
    async_add_entities(devices, True)


class LockSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Lock Switch."""

    entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, _unique_id):
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = _unique_id
        self._attr_name = "Lock switch {}".format(
            coordinator.data[_unique_id]["dev_alias"]
        )

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data[self.unique_id]["attr"].get("lock_switch", False)

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer=DOMAIN,
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        payload = {"attrs": {"lock_switch": 1}}
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.heatzy_client.control_device, self.unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        payload = {"attrs": {"lock_switch": 0}}
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.heatzy_client.control_device, self.unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)

        await self.coordinator.async_request_refresh()
