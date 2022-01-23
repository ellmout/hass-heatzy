"""Climate sensors for Heatzy."""
import logging

from heatzypy.exception import HeatzyException

from homeassistant.components.climate import ClimateEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_PRESET_MODE,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PILOTEV1, PILOTEV2, ELEC_PRO_SOC

MODE_LIST = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
PRESET_LIST = [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Load all Heatzy devices."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices = []
    for device in coordinator.data.values():
        product_key = device.get("product_key")
        if product_key in PILOTEV1:
            devices.append(HeatzyPiloteV1Thermostat(coordinator, device["did"]))
        elif product_key in PILOTEV2 or product_key in ELEC_PRO_SOC:
            devices.append(HeatzyPiloteV2Thermostat(coordinator, device["did"]))
    async_add_entities(devices)


class HeatzyThermostat(CoordinatorEntity, ClimateEntity):
    """Heatzy climate."""

    _attr_hvac_modes = MODE_LIST
    _attr_preset_modes = PRESET_LIST
    _attr_supported_features = SUPPORT_PRESET_MODE
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, coordinator, unique_id):
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = coordinator.data[unique_id]["dev_alias"]

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer=DOMAIN,
            sw_version=self.coordinator.data[self.unique_id].get("wifi_soft_version"),
            model=self.coordinator.data[self.unique_id].get("product_name"),
        )

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        if self.preset_mode == PRESET_NONE:
            return HVAC_MODE_OFF
        return HVAC_MODE_HEAT

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            await self.async_turn_off()
        elif hvac_mode == HVAC_MODE_HEAT:
            await self.async_turn_on()

    async def async_turn_on(self):
        """Turn device on."""
        await self.async_set_preset_mode(PRESET_COMFORT)

    async def async_turn_off(self):
        """Turn device off."""
        await self.async_set_preset_mode(PRESET_NONE)


class HeatzyPiloteV1Thermostat(HeatzyThermostat):
    """Heaty Pilote v1."""

    HEATZY_TO_HA_STATE = {
        "\u8212\u9002": PRESET_COMFORT,
        "\u7ecf\u6d4e": PRESET_ECO,
        "\u89e3\u51bb": PRESET_AWAY,
        "\u505c\u6b62": PRESET_NONE,
    }
    HA_TO_HEATZY_STATE = {
        PRESET_COMFORT: [1, 1, 0],
        PRESET_ECO: [1, 1, 1],
        PRESET_AWAY: [1, 1, 2],
        PRESET_NONE: [1, 1, 3],
    }

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return self.HEATZY_TO_HA_STATE.get(
            self.coordinator.data[self.unique_id].get("attr", {}).get("mode")
        )

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        try:
            await self.coordinator.heatzy_client.control_device(
                self.unique_id,
                {"raw": self.HA_TO_HEATZY_STATE.get(preset_mode)},
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error("Error to set preset mode : %s", error)


class HeatzyPiloteV2Thermostat(HeatzyThermostat):
    """Heaty Pilote v2."""

    # spell-checker:disable
    HEATZY_TO_HA_STATE = {
        "cft": PRESET_COMFORT,
        "eco": PRESET_ECO,
        "fro": PRESET_AWAY,
        "stop": PRESET_NONE,
    }

    HA_TO_HEATZY_STATE = {
        PRESET_COMFORT: "cft",
        PRESET_ECO: "eco",
        PRESET_AWAY: "fro",
        PRESET_NONE: "stop",
    }
    # spell-checker:enable

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return self.HEATZY_TO_HA_STATE.get(
            self.coordinator.data[self.unique_id].get("attr", {}).get("mode")
        )

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id,
                {"attrs": {"mode": self.HA_TO_HEATZY_STATE.get(preset_mode)}},
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error("Error to set preset mode : %s", error)
