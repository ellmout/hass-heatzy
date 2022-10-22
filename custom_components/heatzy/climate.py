"""Climate sensors for Heatzy."""
import logging

from heatzypy.exception import HeatzyException
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HeatzyDataUpdateCoordinator
from .const import DOMAIN, ELEC_PRO_SOC, GLOW, PILOTEV1, PILOTEV2

MODE_LIST = [HVACMode.HEAT, HVACMode.OFF]
PRESET_LIST = [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Load all Heatzy devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = []
    for device in coordinator.data.values():
        product_key = device.get("product_key")
        if product_key in PILOTEV1:
            devices.append(HeatzyPiloteV1Thermostat(coordinator, device["did"]))
        elif product_key in PILOTEV2 or product_key in ELEC_PRO_SOC:
            devices.append(HeatzyPiloteV2Thermostat(coordinator, device["did"]))
        elif product_key in GLOW:
            devices.append(Glowv1Thermostat(coordinator, device["did"]))
    async_add_entities(devices)


class HeatzyThermostat(CoordinatorEntity[HeatzyDataUpdateCoordinator], ClimateEntity):
    """Heatzy climate."""

    _attr_hvac_modes = MODE_LIST
    _attr_preset_modes = PRESET_LIST
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeatzyDataUpdateCoordinator, unique_id):
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
            return HVACMode.OFF
        return HVACMode.HEAT

    async def async_set_hvac_mode(self, hvac_mode: str) -> bool:
        """Set new hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode == HVACMode.HEAT:
            await self.async_turn_on()

    async def async_turn_on(self) -> str:
        """Turn device on."""
        await self.async_set_preset_mode(PRESET_COMFORT)

    async def async_turn_off(self) -> str:
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
    def preset_mode(self) -> str:
        """Return the current preset mode, e.g., home, away, temp."""
        return self.HEATZY_TO_HA_STATE.get(
            self.coordinator.data[self.unique_id].get("attr", {}).get("mode")
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id,
                {"raw": self.HA_TO_HEATZY_STATE.get(preset_mode)},
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error(
                "Set preset mode (%s) %s (%s)", preset_mode, error, self.name
            )


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
    def preset_mode(self) -> str:
        """Return the current preset mode, e.g., home, away, temp."""
        return self.HEATZY_TO_HA_STATE.get(
            self.coordinator.data[self.unique_id].get("attr", {}).get("mode")
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id,
                {"attrs": {"mode": self.HA_TO_HEATZY_STATE.get(preset_mode)}},
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error(
                "Set preset mode (%s) %s (%s)", preset_mode, error, self.name
            )


class Glowv1Thermostat(HeatzyPiloteV2Thermostat):
    """Glow."""

    _attr_supported_features = SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE_RANGE

    @property
    def current_temperature(self) -> float:
        """Return current temperature."""
        cur_tempH = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("cur_tempH")
        )
        cur_tempL = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("cur_tempL")
        )
        return (cur_tempL + (cur_tempH * 255)) / 10

    @property
    def target_temperature_high(self) -> float:
        """Return comfort temperature."""
        cft_tempH = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("cft_tempH", 0)
        )
        cft_tempL = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("cft_tempL", 0)
        )
        return (cft_tempL + (cft_tempH * 255)) / 10

    @property
    def target_temperature_low(self) -> float:
        """Return comfort temperature."""
        eco_tempH = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("eco_tempH", 0)
        )
        eco_tempL = (
            self.coordinator.data[self.unique_id].get("attr", {}).get("eco_tempL", 0)
        )
        return (eco_tempL + (eco_tempH * 255)) / 10

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp_eco = kwargs.get(ATTR_TARGET_TEMP_LOW)
        temp_cft = kwargs.get(ATTR_TARGET_TEMP_HIGH)

        if (temp_eco or temp_cft) is None:
            return

        b_temp_cft = int(temp_cft * 10)
        b_temp_eco = int(temp_eco * 10)

        self.coordinator.data[self.unique_id].get("attr", {})["eco_tempL"] = b_temp_eco
        self.coordinator.data[self.unique_id].get("attr", {})["cft_tempL"] = b_temp_cft

        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id,
                {
                    "attrs": {
                        "cft_tempL": b_temp_cft,
                        "eco_tempL": b_temp_eco,
                    }
                },
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error("Error to set temperature: %s", error)

    async def async_turn_on(self) -> str:
        """Turn device on."""
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id, {"attrs": {"on_off": 1}}
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error("Error to turn on : %s", error)

    async def async_turn_off(self) -> str:
        """Turn device off."""
        try:
            await self.coordinator.heatzy_client.async_control_device(
                self.unique_id, {"attrs": {"on_off": 0}}
            )
            await self.coordinator.async_request_refresh()
        except HeatzyException as error:
            _LOGGER.error("Error to turn off : %s", error)

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        if self.coordinator.data[self.unique_id].get("attr", {}).get("on_off") == 0:
            return HVACMode.OFF
        return HVACMode.HEAT
