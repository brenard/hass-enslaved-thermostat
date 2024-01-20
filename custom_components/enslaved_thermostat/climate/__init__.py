"""Adds support for enslaved thermostat."""
import logging

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
)
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .. import DOMAIN, PLATFORMS
from ..const import (
    CONF_ENSLAVED_THERMOSTATS,
    CONF_INITIAL_ENSLAVED_MODE,
    CONF_INITIAL_MANUAL_HVAC_MODE,
    CONF_INITIAL_MANUAL_TARGET_TEMP,
    CONF_TYPE,
    SERVICE_RESTORE_MANUAL_STATE,
    SERVICE_SET_ENSLAVED_HVAC_MODE,
    SERVICE_SET_ENSLAVED_MODE,
    SERVICE_SET_ENSLAVED_TARGET_TEMP,
    SERVICE_SET_MANUAL_STATE,
    SERVICE_START_SCHEDULER_MODE,
    SERVICE_STOP_SCHEDULER_MODE,
    EnslavedType,
)
from .enslaved import EnslavedMode, EnslavedThermostat
from .master import MasterThermostat
from .schedulable import SchedulableThermostat

log = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HEATER): cv.entity_id,
        vol.Optional(CONF_SENSOR): cv.entity_id,
        vol.Required(CONF_TYPE, default=EnslavedType.ENSLAVED): vol.Coerce(EnslavedType),
        vol.Optional(CONF_NAME): cv.string,
        # For enslaved thermostats
        vol.Optional(CONF_INITIAL_ENSLAVED_MODE): vol.Coerce(EnslavedMode),
        # For master thermostats
        vol.Optional(CONF_ENSLAVED_THERMOSTATS, default=[]): vol.All(
            cv.ensure_list, [cv.entity_id]
        ),
        vol.Optional(CONF_INITIAL_MANUAL_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(CONF_INITIAL_MANUAL_HVAC_MODE): vol.Coerce(HVACMode),
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

    kwargs = {
        "name": config.get(CONF_NAME),
        "min_temp": config.get(CONF_MIN_TEMP),
        "max_temp": config.get(CONF_MAX_TEMP),
        "target_temp": config.get(CONF_TARGET_TEMP),
        "ac_mode": config.get(CONF_AC_MODE),
        "initial_hvac_mode": config.get(CONF_INITIAL_HVAC_MODE),
        "presets": {key: config[value] for key, value in CONF_PRESETS.items() if value in config},
        "precision": config.get(CONF_PRECISION),
        "target_temperature_step": config.get(CONF_TEMP_STEP),
        "unit": hass.config.units.temperature_unit,
        "unique_id": config.get(CONF_UNIQUE_ID),
        "initial_manual_target_temp": config.get(CONF_INITIAL_MANUAL_TARGET_TEMP),
        "initial_manual_hvac_mode": config.get(CONF_INITIAL_MANUAL_HVAC_MODE),
    }

    dev_type = config.get(CONF_TYPE)
    if dev_type == EnslavedType.ENSLAVED:
        kwargs.update(
            {
                "heater_entity_id": config.get(CONF_HEATER),
                "sensor_entity_id": config.get(CONF_SENSOR),
                "min_cycle_duration": config.get(CONF_MIN_DUR),
                "cold_tolerance": config.get(CONF_COLD_TOLERANCE),
                "hot_tolerance": config.get(CONF_HOT_TOLERANCE),
                "keep_alive": config.get(CONF_KEEP_ALIVE),
                "initial_enslaved_mode": config.get(CONF_INITIAL_ENSLAVED_MODE),
            }
        )
        async_add_entities([EnslavedThermostat(**kwargs)])
    elif dev_type == EnslavedType.MASTER:
        kwargs.update(
            {
                "enslaved_thermostats": config.get(CONF_ENSLAVED_THERMOSTATS),
            }
        )
        async_add_entities([MasterThermostat(**kwargs)])
    elif dev_type == EnslavedType.SCHEDULABLE:
        kwargs.update(
            {
                "enslaved_thermostats": config.get(CONF_ENSLAVED_THERMOSTATS),
            }
        )
        async_add_entities([SchedulableThermostat(**kwargs)])

    log.debug("Register enslaved thermostats services")
    platform = async_get_current_platform()

    await async_register_services(platform)


async def async_register_services(platform) -> None:
    """Register enslaved thermostat services."""

    log.debug("Register enslaved thermostats services")
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

    platform.async_register_entity_service(
        SERVICE_START_SCHEDULER_MODE,
        {
            vol.Required("temperature"): vol.Coerce(float),
            vol.Optional("hvac_mode"): vol.Coerce(HVACMode),
        },
        "async_start_scheduler_mode",
    )

    platform.async_register_entity_service(
        SERVICE_STOP_SCHEDULER_MODE,
        {},
        "async_stop_scheduler_mode",
    )

    platform.async_register_entity_service(
        SERVICE_SET_MANUAL_STATE,
        {
            vol.Optional("temperature"): vol.Coerce(float),
            vol.Optional("hvac_mode"): vol.Coerce(HVACMode),
        },
        "async_set_manual_state",
    )

    platform.async_register_entity_service(
        SERVICE_RESTORE_MANUAL_STATE,
        {},
        "async_restore_manual_state",
    )
