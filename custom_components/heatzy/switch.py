"""Sensors for Heatzy."""
import logging

from heatzypy.exception import HeatzyException
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HeatzyDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = []
    for device in coordinator.data.values():
        devices.append(LockSwitchEntity(coordinator, device["did"]))
    async_add_entities(devices, True)


class LockSwitchEntity(CoordinatorEntity[HeatzyDataUpdateCoordinator], SwitchEntity):
    """Lock Switch."""

    entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeatzyDataUpdateCoordinator, did: str):
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = did
        self._attr_name = "Lock switch {}".format(coordinator.data[did]["dev_alias"])

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.coordinator.data[self.unique_id]["attr"].get("lock_switch")

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer=DOMAIN,
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        payload = {"attrs": {"lock_switch": 1}}
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        payload = {"attrs": {"lock_switch": 0}}
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id, payload
            )
        except HeatzyException as error:
            _LOGGER.error("Error to lock pilot : %s", error)

        await self.coordinator.async_request_refresh()
