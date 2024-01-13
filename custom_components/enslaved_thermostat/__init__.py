"""
Custom integration to implement enslaved thermostat in Home Assistant.

For more details about this integration, please refer to
https://github.com/brenard/hass-enslaved-thermostat
"""
from enum import IntFlag

from homeassistant.const import Platform

DOMAIN = "enslaved_thermostat"
PLATFORMS = [Platform.CLIMATE]


class EnslavedThermostatEntityFeature(IntFlag):
    """Supported features of the enslaved thermostat entity."""

    ENSLAVES_MODE = 1
