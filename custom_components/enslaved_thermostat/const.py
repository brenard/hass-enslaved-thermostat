"""Component constants"""

from enum import StrEnum

DEFAULT_ENSLAVED_THERMOSTAT_NAME = "Enslaved Thermostat"
DEFAULT_MASTER_THERMOSTAT_NAME = "Master Thermostat"

CONF_INITIAL_ENSLAVED_MODE = "initial_enslaved_mode"
CONF_TYPE = "type"
CONF_ENSLAVED_THERMOSTATS = "enslaved_thermostats"
CONF_INITIAL_MANUAL_TARGET_TEMP = "initial_manual_target_temp"
CONF_INITIAL_MANUAL_HVAC_MODE = "initial_manual_hvac_mode"

ATTR_ENSLAVED_MODE = "enslaved_mode"
ATTR_ENSLAVED_TARGET_TEMP = "enslaved_target_temp"
ATTR_ENSLAVED_HVAC_MODE = "enslaved_hvac_mode"
ATTR_ENSLAVED_IN_SCHEDULER_MODE = "in_scheduler_mode"
ATTR_ENSLAVED_SCHEDULER_PREV_TARGET_TEMP = "scheduler_previous_target_temp"
ATTR_ENSLAVED_SCHEDULER_PREV_HVAC_MODE = "scheduler_previous_hvac_mode"
ATTR_MANUAL_TARGET_TEMP = "manual_target_temp"
ATTR_MANUAL_HAVC_MODE = "manual_hvac_mode"
ATTR_SCHEDULER_PREV_STATE = "scheduler_previous_state"


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
SERVICE_START_SCHEDULER_MODE = "start_scheduler_mode"
SERVICE_STOP_SCHEDULER_MODE = "stop_scheduler_mode"
SERVICE_SET_MANUAL_STATE = "set_manual_state"
