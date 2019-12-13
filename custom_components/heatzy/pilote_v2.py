import logging

from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (HVAC_MODE_HEAT,
                                                    HVAC_MODE_OFF,
                                                    CURRENT_HVAC_HEAT,
                                                    CURRENT_HVAC_OFF,
                                                    PRESET_AWAY,
                                                    PRESET_COMFORT,
                                                    PRESET_ECO,
                                                    PRESET_NONE,
                                                    SUPPORT_PRESET_MODE)
from homeassistant.const import TEMP_CELSIUS, STATE_OFF, STATE_ON


HEATZY_TO_HA_STATE = {
    'cft': PRESET_COMFORT,
    'eco': PRESET_ECO,
    'fro': PRESET_AWAY,
    'stop': PRESET_NONE,
}

HA_TO_HEATZY_STATE = {
    PRESET_COMFORT: 'cft',
    PRESET_ECO: 'eco',
    PRESET_AWAY: 'fro',
    PRESET_NONE: 'stop',
}

MODE_LIST = [HVAC_MODE_HEAT, HVAC_MODE_OFF, STATE_ON]
PRESET_LIST = [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY]

_LOGGER = logging.getLogger(__name__)


class HeatzyPiloteV2Thermostat(ClimateDevice):
    def __init__(self, api, device):
        self._api = api
        self._device = device
        self._force_update = False

    @property
    def state(self):
        """Return the current state."""
        return self.preset_mode
        
    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_PRESET_MODE

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device.get('did')

    @property
    def name(self):
        return self._device.get('dev_alias')

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return MODE_LIST

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self.preset_mode == PRESET_NONE:
            return HVAC_MODE_OFF
        return STATE_ON

    @property
    def preset_modes(self):
        """Return a list of available preset modes.
        Requires SUPPORT_PRESET_MODE.
        """
        return PRESET_LIST

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp.
        Requires SUPPORT_PRESET_MODE.
        """
        return HEATZY_TO_HA_STATE.get(self._device.get('attr').get('mode'))

    @property
    def hvac_action(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self.preset_mode == PRESET_NONE:
            return CURRENT_HVAC_OFF
        return CURRENT_HVAC_HEAT

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        _LOGGER.debug("Set PRESET MODE : {}".format(preset_mode))
        await self._api.async_control_device(self.unique_id, {
            'attrs': {
                'mode': HA_TO_HEATZY_STATE.get(preset_mode),
            },
        })

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        _LOGGER.debug("Set HVAC MODE : {}".format(hvac_mode))
        if hvac_mode == HVAC_MODE_OFF or hvac_mode == STATE_OFF:
            await self.async_turn_off()
        elif hvac_mode == HVAC_MODE_HEAT or hvac_mode == STATE_ON:
            await self.async_turn_on()

    async def async_turn_on(self):
        """Turn device on."""
        _LOGGER.debug("HVAC Turn On")
        await self._api.async_control_device(self.unique_id, {'attrs': {'mode': 'cft',},})

    async def async_turn_off(self):
        """Turn device off."""
        _LOGGER.debug("HVAC Turn off")
        await self._api.async_control_device(self.unique_id, {'attrs': {'mode': 'stop',},})

    async def async_update(self):
        """Get the latest state from the thermostat."""
        self._device = await self._api.async_get_device(self.unique_id)
