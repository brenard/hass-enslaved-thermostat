"""Adds support for master thermostat."""
import logging
from typing import Any

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from ..const import (
    ATTR_ENSLAVED_MODE,
    DEFAULT_MASTER_THERMOSTAT_NAME,
    SERVICE_SET_ENSLAVED_HVAC_MODE,
    SERVICE_SET_ENSLAVED_TARGET_TEMP,
    EnslavedMode,
)
from .common import FakeEnslavedGenericThermostat

log = logging.getLogger(__name__)


class MasterThermostat(FakeEnslavedGenericThermostat):
    """Representation of an Master Thermostat device"""

    _default_name = DEFAULT_MASTER_THERMOSTAT_NAME

    @staticmethod
    def _enslaved_thermostat_is_handled(state):
        """Check if the enslaved thermostat is handled based on its current state"""
        return state.attributes.get(ATTR_ENSLAVED_MODE) == EnslavedMode.AUTO

    #
    # Override GenericThermostat methods to set HVAC mode and target temperature to control enslaved
    # thermostats
    #

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        log.debug("Set HVAC mode to %s", hvac_mode)
        await super().async_set_hvac_mode(hvac_mode)
        await self._async_call_enslaved_thermostats_service(
            SERVICE_SET_ENSLAVED_HVAC_MODE, {"mode": self.hvac_mode}
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set temperature method"""
        log.debug("Set temperature to %s", kwargs.get(ATTR_TEMPERATURE))
        await super().async_set_temperature(**kwargs)
        await self._async_call_enslaved_thermostats_service(
            SERVICE_SET_ENSLAVED_TARGET_TEMP, {"temperature": self.target_temperature}
        )
