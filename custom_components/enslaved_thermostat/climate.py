"""Adds support for enslaved thermostat."""
import logging
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, final

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.generic_thermostat.climate import (
    CONF_AC_MODE,
    CONF_COLD_TOLERANCE,
    CONF_HEATER,
    CONF_HOT_TOLERANCE,
    CONF_INITIAL_HVAC_MODE,
    CONF_KEEP_ALIVE,
    CONF_MAX_TEMP,
    CONF_MIN_DUR,
    CONF_MIN_TEMP,
    CONF_PRECISION,
    CONF_PRESETS,
    CONF_SENSOR,
    CONF_TARGET_TEMP,
    CONF_TEMP_STEP,
    PLATFORM_SCHEMA,
    GenericThermostat,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import ExtraStoredData
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PLATFORMS

log = logging.getLogger(__name__)

DEFAULT_NAME = "Enslaved Thermostat"

CONF_INITIAL_ENSLAVED_MODE = "initial_enslaved_mode"


class EnslavedMode(StrEnum):
    """Enslaved mode for enslaved thermostat devices."""

    # Auto: used enslaved target temperature and HVAC mode
    AUTO = "auto"

    # Manual: let user used this thermostat as a regular climate device
    MANUAL = "manual"

    # Off: force thermostat to OFF
    OFF = "off"


ENSLAVED_MODES = [cls.value for cls in EnslavedMode]
DEFAULT_ENSLAVED_MODE = EnslavedMode.MANUAL

SERVICE_SET_ENSLAVED_MODE = "set_enslaved_mode"
SERVICE_SET_ENSLAVED_TARGET_TEMP = "set_enslaved_target_temperature"
SERVICE_SET_ENSLAVED_HVAC_MODE = "set_enslaved_hvac_mode"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_INITIAL_ENSLAVED_MODE): vol.Coerce(EnslavedMode),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic thermostat platform."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    heater_entity_id = config.get(CONF_HEATER)
    sensor_entity_id = config.get(CONF_SENSOR)
    min_temp = config.get(CONF_MIN_TEMP)
    max_temp = config.get(CONF_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    ac_mode = config.get(CONF_AC_MODE)
    min_cycle_duration = config.get(CONF_MIN_DUR)
    cold_tolerance = config.get(CONF_COLD_TOLERANCE)
    hot_tolerance = config.get(CONF_HOT_TOLERANCE)
    keep_alive = config.get(CONF_KEEP_ALIVE)
    initial_hvac_mode = config.get(CONF_INITIAL_HVAC_MODE)
    initial_enslaved_mode = config.get(CONF_INITIAL_ENSLAVED_MODE)
    presets = {key: config[value] for key, value in CONF_PRESETS.items() if value in config}
    precision = config.get(CONF_PRECISION)
    target_temperature_step = config.get(CONF_TEMP_STEP)
    unit = hass.config.units.temperature_unit
    unique_id = config.get(CONF_UNIQUE_ID)

    async_add_entities(
        [
            EnslavedThermostat(
                name,
                heater_entity_id,
                sensor_entity_id,
                min_temp,
                max_temp,
                target_temp,
                ac_mode,
                min_cycle_duration,
                cold_tolerance,
                hot_tolerance,
                keep_alive,
                initial_hvac_mode,
                presets,
                precision,
                target_temperature_step,
                unit,
                unique_id,
                initial_enslaved_mode,
            )
        ]
    )

    log.debug("Register enslaved thermostats services")
    platform = async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_ENSLAVED_MODE,
        {
            vol.Required("mode"): vol.Coerce(EnslavedMode),
            vol.Optional("temperature"): vol.Coerce(float),
            vol.Optional("hvac_mode"): vol.Coerce(HVACMode),
        },
        "async_set_enslaved_mode",
    )

    platform.async_register_entity_service(
        SERVICE_SET_ENSLAVED_TARGET_TEMP,
        {
            vol.Required("temperature"): vol.Coerce(float),
        },
        "async_set_enslaved_target_temp",
    )

    platform.async_register_entity_service(
        SERVICE_SET_ENSLAVED_HVAC_MODE,
        {
            vol.Required("mode"): vol.Coerce(HVACMode),
        },
        "async_set_enslaved_hvac_mode",
    )


@dataclass
class EnslavedThermostatExtraStoredData(ExtraStoredData):
    """Object to hold enslaved thermostat extra stored data."""

    enslaved_mode: str | None = None
    enslaved_target_temp: float | None = None
    enslaved_hvac_mode: HVACMode | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the text data."""
        return asdict(self)


class EnslavedThermostat(GenericThermostat):
    """Representation of an Enslaved Thermostat device"""

    _enslaved_target_temp = None
    _enslaved_hvac_mode = None

    def __init__(
        self,
        name,
        heater_entity_id,
        sensor_entity_id,
        min_temp,
        max_temp,
        target_temp,
        ac_mode,
        min_cycle_duration,
        cold_tolerance,
        hot_tolerance,
        keep_alive,
        initial_hvac_mode,
        presets,
        precision,
        target_temperature_step,
        unit,
        unique_id,
        initial_enslaved_mode,
    ):
        """Initialize the thermostat."""
        log.debug("Initialize enslaved thermostat %s", name)
        super().__init__(
            name,
            heater_entity_id,
            sensor_entity_id,
            min_temp,
            max_temp,
            target_temp,
            ac_mode,
            min_cycle_duration,
            cold_tolerance,
            hot_tolerance,
            keep_alive,
            initial_hvac_mode,
            presets,
            precision,
            target_temperature_step,
            unit,
            unique_id,
        )
        if initial_enslaved_mode and initial_enslaved_mode not in ENSLAVED_MODES:
            raise ValueError(
                f"Got unsupported initial_enslaved_mode {initial_enslaved_mode}. Must be one of"
                f" {ENSLAVED_MODES}"
            )
        self._enslaved_mode = (
            initial_enslaved_mode if initial_enslaved_mode else DEFAULT_ENSLAVED_MODE
        )

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        """Return entity extra state data to be restored."""
        return EnslavedThermostatExtraStoredData(
            enslaved_mode=self.enslaved_mode,
            enslaved_target_temp=self.enslaved_target_temp,
            enslaved_hvac_mode=self.enslaved_hvac_mode,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        # Retrieve and restore enslaved mode info from last known state
        last_extra_data = await self.async_get_last_extra_data()
        if last_extra_data is not None:
            last_extra_data = last_extra_data.as_dict()
            log.debug("Last extra data: %s", last_extra_data)
            self._enslaved_mode = last_extra_data["enslaved_mode"]
            self._enslaved_target_temp = last_extra_data["enslaved_target_temp"]
            self._enslaved_hvac_mode = last_extra_data["enslaved_hvac_mode"]
        await super().async_added_to_hass()

    @property
    def enslaved_mode(self):
        """Return current enslaved mode."""
        return self._enslaved_mode

    @property
    def enslaved_target_temp(self):
        """Return current enslaved mode."""
        return self._enslaved_target_temp if self._enslaved_target_temp else self._target_temp

    @property
    def enslaved_hvac_mode(self):
        """Return current enslaved HVAC mode."""
        return self._enslaved_hvac_mode if self._enslaved_hvac_mode else self.hvac_mode

    @final
    @property
    def state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        data = super().state_attributes
        data.update(
            {
                "enslaved_mode": self.enslaved_mode,
                "enslaved_target_temp": self.enslaved_target_temp,
                "enslaved_hvac_mode": self.enslaved_hvac_mode,
            }
        )
        return data

    async def async_set_enslaved_mode(self, mode, temperature=None, hvac_mode=None):
        """Set current enslaved mode."""
        log.debug("async_set_enslaved_mode(%s, %s, %s)", mode, temperature, hvac_mode)
        if mode not in ENSLAVED_MODES:
            raise ValueError(
                f"Got unsupported enslaved_mode {mode}. Must be one of" f" {ENSLAVED_MODES}"
            )
        self._enslaved_mode = mode

        if temperature is not None:
            await self.async_set_enslaved_target_temp(temperature)

        if hvac_mode is not None:
            await self.async_set_enslaved_hvac_mode(hvac_mode)

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
        if self.enslaved_mode == EnslavedMode.AUTO:
            await self._async_set_hvac_mode(mode)
        # Ensure to update state after changing the enslaved HVAC mode
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        log.debug("Set HVAC mode to %s and enslaved mode to manual", hvac_mode)
        await self._async_set_hvac_mode(hvac_mode)
        await self.async_set_enslaved_mode(EnslavedMode.MANUAL)

    async def _async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Original GenericThermostat set HVAC mode."""
        await super().async_set_hvac_mode(hvac_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set temperature method"""
        log.debug("Set temperature to %s and enslaved mode to manual", kwargs.get(ATTR_TEMPERATURE))
        await self._async_set_temperature(**kwargs)
        await self.async_set_enslaved_mode(EnslavedMode.MANUAL)

    async def _async_set_temperature(self, **kwargs: Any) -> None:
        """Original GenericThermostat set temperature method"""
        await super().async_set_temperature(**kwargs)
