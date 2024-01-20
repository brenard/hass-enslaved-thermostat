"""Adds support for schedulable thermostat."""
import logging
from typing import Any

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from ..const import ATTR_ENSLAVED_IN_SCHEDULER_MODE, DEFAULT_SCHEDULABLE_THERMOSTAT_NAME
from .common import FakeEnslavedGenericThermostat

log = logging.getLogger(__name__)


class SchedulableThermostat(FakeEnslavedGenericThermostat):
    """Representation of an Schedulable Thermostat device"""

    _default_name = DEFAULT_SCHEDULABLE_THERMOSTAT_NAME

    @staticmethod
    def _enslaved_thermostat_is_handled(state):
        """Check if the enslaved thermostat is handled based on its current state"""
        return state.attributes.get(ATTR_ENSLAVED_IN_SCHEDULER_MODE)

    #
    # Override GenericThermostat methods to set HVAC mode and target temperature to control enslaved
    # thermostats
    #

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        log.debug("Set HVAC mode to %s", hvac_mode)
        await super().async_set_hvac_mode(hvac_mode)
        if self.hvac_mode == HVACMode.OFF:
            await self.async_stop_scheduler_mode()
        else:
            await self.async_start_scheduler_mode()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set temperature method"""
        log.debug("Set temperature to %s", kwargs.get(ATTR_TEMPERATURE))
        await super().async_set_temperature(**kwargs)
        if self.hvac_mode != HVACMode.OFF:
            await self.async_start_scheduler_mode()
