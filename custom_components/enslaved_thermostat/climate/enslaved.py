"""Adds support for enslaved thermostat."""
import logging
from dataclasses import dataclass
from typing import Any, final

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.helpers.restore_state import ExtraStoredData

try:
    from homeassistant.exceptions import ServiceValidationError
except ImportError:
    from homeassistant.exceptions import HomeAssistantError as ServiceValidationError

from ..const import (
    ATTR_ENSLAVED_HVAC_MODE,
    ATTR_ENSLAVED_IN_SCHEDULER_MODE,
    ATTR_ENSLAVED_MODE,
    ATTR_ENSLAVED_SCHEDULER_PREV_HVAC_MODE,
    ATTR_ENSLAVED_SCHEDULER_PREV_TARGET_TEMP,
    ATTR_ENSLAVED_TARGET_TEMP,
    ATTR_SCHEDULER_PREV_STATE,
    DEFAULT_ENSLAVED_MODE,
    DEFAULT_ENSLAVED_THERMOSTAT_NAME,
    ENSLAVED_MODES,
    EnslavedMode,
)
from .common import EnslavedGenericThermostat, EnslavedGenericThermostatExtraStoredData

log = logging.getLogger(__name__)


@dataclass
class EnslavedThermostatExtraStoredData(EnslavedGenericThermostatExtraStoredData):
    """Object to hold enslaved thermostat extra stored data."""

    enslaved_mode: str | None = None
    enslaved_target_temp: float | None = None
    enslaved_hvac_mode: HVACMode | None = None
    scheduler_previous_state: dict | None = None


class EnslavedThermostat(EnslavedGenericThermostat):
    """Representation of an Enslaved Thermostat device"""

    _default_name = DEFAULT_ENSLAVED_THERMOSTAT_NAME

    _enslaved_target_temp = None
    _enslaved_hvac_mode = None
    _scheduler_previous_state = None

    def __init__(self, **kwargs):
        """Initialize the thermostat."""
        super().__init__(**kwargs)
        assert kwargs[
            "heater_entity_id"
        ], f"No heater configured for enslaved thermostat {kwargs['name']}"
        assert kwargs[
            "sensor_entity_id"
        ], f"No sensor configured for enslaved thermostat {kwargs['name']}"

        initial_enslaved_mode = kwargs.get("initial_enslaved_mode")
        if initial_enslaved_mode and initial_enslaved_mode not in ENSLAVED_MODES:
            raise ValueError(
                f"Got unsupported initial_enslaved_mode {initial_enslaved_mode}. Must be one of"
                f" {ENSLAVED_MODES}"
            )
        self._enslaved_mode = (
            initial_enslaved_mode if initial_enslaved_mode else DEFAULT_ENSLAVED_MODE
        )

    #
    # Implement methods to allow saving and restore custom state attributes
    #

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        """Return entity extra state data to be restored."""
        return EnslavedThermostatExtraStoredData(
            enslaved_mode=self.enslaved_mode,
            enslaved_target_temp=self.enslaved_target_temp,
            enslaved_hvac_mode=self.enslaved_hvac_mode,
            scheduler_previous_state=self._scheduler_previous_state,
            **super().extra_restore_state_data.as_dict(),
        )

    def _restore_last_extra_data(self, last_extra_data):
        """Restore last extra data"""
        super()._restore_last_extra_data(last_extra_data)
        self._enslaved_mode = last_extra_data.get(ATTR_ENSLAVED_MODE)
        self._enslaved_target_temp = last_extra_data.get(ATTR_ENSLAVED_TARGET_TEMP)
        self._enslaved_hvac_mode = last_extra_data.get(ATTR_ENSLAVED_HVAC_MODE)
        self._scheduler_previous_state = last_extra_data.get(ATTR_SCHEDULER_PREV_STATE)

    #
    # Append custom state attributes in the entity's state attributes
    #

    @final
    @property
    def state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        log.debug("Compute state attributes")
        data = super().state_attributes
        data.update(
            {
                ATTR_ENSLAVED_MODE: self.enslaved_mode,
                ATTR_ENSLAVED_TARGET_TEMP: self.enslaved_target_temp,
                ATTR_ENSLAVED_HVAC_MODE: self.enslaved_hvac_mode,
                ATTR_ENSLAVED_IN_SCHEDULER_MODE: self.in_scheduler_mode,
                ATTR_ENSLAVED_SCHEDULER_PREV_TARGET_TEMP: (
                    self._scheduler_previous_state["temperature"]
                    if self._scheduler_previous_state
                    else None
                ),
                ATTR_ENSLAVED_SCHEDULER_PREV_HVAC_MODE: (
                    self._scheduler_previous_state["hvac_mode"]
                    if self._scheduler_previous_state
                    else None
                ),
            }
        )
        return data

    #
    # Implement methods to control the enslaved mode
    #
    # Note: these methods are callable through custom integration services registered in
    # async_setup_platform() and described in services.yaml file.
    #

    @property
    def enslaved_mode(self):
        """Return current enslaved mode."""
        return self._enslaved_mode

    def assert_not_in_enslaved_off_mode(self):
        """
        Verify the thermostat is not in enslaved force OFF mode. Raise a ServiceValidationError
        exception otherwise.
        """
        if self.enslaved_mode == EnslavedMode.OFF:
            raise ServiceValidationError(
                "This thermostat is currently in enslaved force OFF mode, can't control it without"
                " leaving this mode first."
            )

    @property
    def enslaved_target_temp(self):
        """Return current enslaved mode."""
        return self._enslaved_target_temp if self._enslaved_target_temp else self._target_temp

    @property
    def enslaved_hvac_mode(self):
        """Return current enslaved HVAC mode."""
        return self._enslaved_hvac_mode if self._enslaved_hvac_mode else self.hvac_mode

    async def async_set_enslaved_mode(self, mode=None, temperature=None, hvac_mode=None):
        """Set current enslaved mode."""
        log.debug("async_set_enslaved_mode(%s, %s, %s)", mode, temperature, hvac_mode)
        if mode is not None:
            if mode not in ENSLAVED_MODES:
                raise ValueError(
                    f"Got unsupported enslaved_mode {mode}. Must be one of" f" {ENSLAVED_MODES}"
                )
            if self._enslaved_mode != mode:
                # Save manual state if we leave the manual mode
                if self._enslaved_mode == EnslavedMode.MANUAL:
                    self.manual_target_temp = self.target_temperature
                    self.manual_hvac_mode = self.hvac_mode
                self._enslaved_mode = mode
                # Restore the manual
                if mode == EnslavedMode.MANUAL:
                    await self.async_restore_manual_state()

        if temperature is not None:
            await self.async_set_enslaved_target_temp(temperature)

        if hvac_mode is not None:
            await self.async_set_enslaved_hvac_mode(hvac_mode)

        # Do not apply new state if thermostat is currently in scheduler mode
        if self.in_scheduler_mode:
            return

        if self.enslaved_mode == EnslavedMode.AUTO:
            await self._async_set_temperature(temperature=self.enslaved_target_temp)
            await self._async_set_hvac_mode(self.enslaved_hvac_mode)
        elif self.enslaved_mode == EnslavedMode.OFF:
            await self._async_set_hvac_mode(HVACMode.OFF)

        # Ensure to update state after changing the enslaved mode
        self.async_write_ha_state()

    async def async_set_enslaved_target_temp(self, temperature):
        """Set current enslaved target temperature."""
        log.debug("async_set_enslaved_target_temp(%s)", temperature)
        if self.min_temp > temperature or self.max_temp < temperature:
            raise ValueError(
                f"Got unsupported enslaved_target_temp {temperature}. Must be between"
                f" {self.min_temp} and {self.max_temp}."
            )
        self._enslaved_target_temp = temperature

        # Do not apply new state if thermostat is currently in scheduler mode
        if self.in_scheduler_mode:
            return

        if self.enslaved_mode == EnslavedMode.AUTO:
            await self._async_set_temperature(temperature=temperature)
        # Ensure to update state after changing the enslaved target temperature
        self.async_write_ha_state()

    async def async_set_enslaved_hvac_mode(self, mode):
        """Set current enslaved HVAC mode."""
        log.debug("async_set_enslaved_hvac_mode(%s)", mode)
        if mode not in self.hvac_modes:
            raise ValueError(
                f"Got unsupported enslaved_hvac_mode {mode}. Must be one of {self.hvac_modes}."
            )
        self._enslaved_hvac_mode = mode

        # Do not apply new state if thermostat is currently in scheduler mode
        if self.in_scheduler_mode:
            return

        if self.enslaved_mode == EnslavedMode.AUTO:
            await self._async_set_hvac_mode(mode)
        # Ensure to update state after changing the enslaved HVAC mode
        self.async_write_ha_state()

    #
    # Implement methods to control the scheduler mode
    #
    # Note: these methods are callable through custom integration services registered in
    # async_setup_platform() and described in services.yaml file.
    #

    @property
    def in_scheduler_mode(self):
        """Return True if thermostat is currently in scheduler mode, False otherwise."""
        return bool(self._scheduler_previous_state)

    def assert_not_in_scheduler_mode(self):
        """
        Verify the thermostat is not in scheduler mode. Raise a ServiceValidationError exception
        otherwise.
        """
        if self.in_scheduler_mode:
            raise ServiceValidationError(
                "This thermostat is currently in scheduler mode, can't control it without leaving"
                " this mode first."
            )

    async def async_start_scheduler_mode(self, temperature, hvac_mode=None):
        """
        Start scheduler mode: apply specified heating parameters and store current state in
        self._scheduler_previous_state.
        """
        log.debug("async_start_scheduler_mode(%s, %s)", temperature, hvac_mode)
        current_state = {
            "temperature": self._target_temp,
            "hvac_mode": self.hvac_mode,
        }
        try:
            await self._async_set_temperature(temperature=temperature)
            await self._async_set_hvac_mode(hvac_mode if hvac_mode is not None else HVACMode.HEAT)
        except ValueError:
            log.warning(
                "Fail to start scheduler mode with provided parameters, restore previous state"
            )
            await self._async_set_temperature(temperature=current_state["temperature"])
            await self._async_set_hvac_mode(current_state["hvac_mode"])
            raise

        if not self._scheduler_previous_state:
            self._scheduler_previous_state = current_state

        # Apply enslaved mode state if it changed during thermostat was in scheduler mode
        await self.async_set_enslaved_mode()

        # Ensure to update state after changing the enslaved mode
        self.async_write_ha_state()

    async def async_stop_scheduler_mode(self):
        """
        Start scheduler mode: restore previous state from self._scheduler_previous_state and clean
        it to leave scheduler mode.
        """
        log.debug("async_stop_scheduler_mode()")
        if not self._scheduler_previous_state:
            raise ServiceValidationError("This thermostat is not currently in scheduler mode.")
        current_state = {
            "temperature": self._target_temp,
            "hvac_mode": self.hvac_mode,
        }
        try:
            await self._async_set_temperature(
                temperature=self._scheduler_previous_state["temperature"]
            )
            await self._async_set_hvac_mode(self._scheduler_previous_state["hvac_mode"])
        except ValueError:
            log.warning(
                "Fail to restore the state before the scheduler was stated, restore previous state"
            )
            await self._async_set_temperature(temperature=current_state["temperature"])
            await self._async_set_hvac_mode(current_state["hvac_mode"])
            raise

        # Clean previous state to leave scheduler mode
        self._scheduler_previous_state = None

        # Ensure to update state after changing the enslaved mode
        self.async_write_ha_state()

    #
    # Override GenericThermostat methods to set HVAC mode and target temperature to manage the
    # current scheduler and enslaved mode in case on manual action on the thermostat:
    # - forbidden change in scheduler mode or in force OFF enslaved mode
    # - switch in manual enslaved mode otherwise
    # Note: Keep access to original methods by adding private methods.
    #

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        self.assert_not_in_scheduler_mode()
        self.assert_not_in_enslaved_off_mode()
        log.debug("Set HVAC mode to %s and enslaved mode to manual", hvac_mode)
        await self._async_set_hvac_mode(hvac_mode)
        await self.async_set_enslaved_mode(EnslavedMode.MANUAL)

    async def _async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Original GenericThermostat set HVAC mode."""
        await super().async_set_hvac_mode(hvac_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set temperature method"""
        self.assert_not_in_scheduler_mode()
        self.assert_not_in_enslaved_off_mode()
        log.debug("Set temperature to %s and enslaved mode to manual", kwargs.get(ATTR_TEMPERATURE))
        await self._async_set_temperature(**kwargs)
        await self.async_set_enslaved_mode(EnslavedMode.MANUAL)

    async def _async_set_temperature(self, **kwargs: Any) -> None:
        """Original GenericThermostat set temperature method"""
        await super().async_set_temperature(**kwargs)

    #
    # Override restore_manual_state() method to respect the scheduler mode and switch to enslaved
    # manual mode if not already set.
    #

    async def async_restore_manual_state(self):
        """
        Restore manual state if we are not in scheduler mode.
        Note: set enslaved mode to manual if not set.
        """
        self.assert_not_in_scheduler_mode()
        log.debug("async_restore_manual_state()")
        if self.enslaved_mode != EnslavedMode.MANUAL:
            self.set_enslaved_mode(EnslavedMode.MANUAL)
        # If we are in scheduler mode, do not restore manual state, but override state to restore
        # when we will leave the scheduler mode
        if self.in_scheduler_mode:
            self._scheduler_previous_state = {
                "temperature": (
                    self.manual_target_temp
                    if self.manual_target_temp
                    else self._scheduler_previous_state["temperature"]
                ),
                "hvac_mode": (
                    self.manual_hvac_mode
                    if self.manual_hvac_mode
                    else self._scheduler_previous_state["hvac_mode"]
                ),
            }
        else:
            super().restore_manual_state()
