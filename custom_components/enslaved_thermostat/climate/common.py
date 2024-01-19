"""Common suff for Enslaved Thermostat device"""
import logging
from dataclasses import asdict, dataclass
from typing import Any

from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
)
from homeassistant.components.generic_thermostat.climate import GenericThermostat
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import EventStateChangedData, async_track_state_change_event
from homeassistant.helpers.restore_state import ExtraStoredData
from homeassistant.helpers.typing import EventType

from .. import DOMAIN
from ..const import (
    ATTR_MANUAL_HAVC_MODE,
    ATTR_MANUAL_TARGET_TEMP,
    SERVICE_SET_ENSLAVED_MODE,
    SERVICE_START_SCHEDULER_MODE,
    SERVICE_STOP_SCHEDULER_MODE,
    EnslavedMode,
)

log = logging.getLogger(__name__)


class EnslavedGenericThermostat(GenericThermostat):
    """Common class for Enslaved Thermostat device"""

    _default_name = None

    manual_target_temp = None
    manual_hvac_mode = None

    def __init__(self, **kwargs):
        """Initialize the thermostat."""
        kwargs["name"] = kwargs.get("name", self._default_name)
        log.debug("Initialize %s %s", self.__class__.__name__, kwargs["name"])
        super().__init__(
            kwargs.get("name", self._default_name),
            kwargs.get("heater_entity_id"),
            kwargs.get("sensor_entity_id"),
            kwargs.get("min_temp"),
            kwargs.get("max_temp"),
            kwargs.get("target_temp"),
            kwargs.get("ac_mode"),
            kwargs.get("min_cycle_duration"),
            kwargs.get("cold_tolerance"),
            kwargs.get("hot_tolerance"),
            kwargs.get("keep_alive"),
            kwargs.get("initial_hvac_mode"),
            kwargs.get("presets"),
            kwargs.get("precision"),
            kwargs.get("target_temperature_step"),
            kwargs.get("unit"),
            kwargs.get("unique_id"),
        )
        self.manual_target_temp = kwargs.get("initial_manual_target_temp")
        self.manual_hvac_mode = kwargs.get("initial_manual_hvac_mode")

    #
    # Implement methods to allow saving and restore custom state attributes
    #

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        """Return entity extra state data to be restored."""
        return EnslavedGenericThermostatExtraStoredData(
            manual_target_temp=self.manual_target_temp,
            manual_hvac_mode=self.manual_hvac_mode,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        # Retrieve and restore enslaved mode info from last known state
        await self.async_restore_last_extra_data()
        await super().async_added_to_hass()

    async def async_restore_last_extra_data(self):
        """Restore last extra data"""
        last_extra_data = await self.async_get_last_extra_data()
        if last_extra_data is not None:
            last_extra_data = last_extra_data.as_dict()
            log.debug("Last extra data: %s", last_extra_data)
            self._restore_last_extra_data(last_extra_data)

    def _restore_last_extra_data(self, last_extra_data):
        """Restore last extra data"""
        self.manual_target_temp = last_extra_data.get(ATTR_MANUAL_TARGET_TEMP)
        self.manual_hvac_mode = last_extra_data.get(ATTR_MANUAL_HAVC_MODE)

    #
    # Append custom state attributes in the entity's state attributes
    #

    @property
    def state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        log.debug("Compute state attributes")
        data = super().state_attributes
        data.update(
            {
                ATTR_MANUAL_TARGET_TEMP: self.manual_target_temp,
                ATTR_MANUAL_HAVC_MODE: self.manual_hvac_mode,
            }
        )
        return data

    #
    # Implement method to control the manual state
    #
    # Note: this method is callable througt custom integration services registered in
    # async_setup_platform() and described in services.yaml file.
    #

    async def async_set_manual_state(self, temperature=None, hvac_mode=None):
        """Set current manual state."""
        log.debug("async_set_manual_state(%s, %s)", temperature, hvac_mode)
        if temperature is not None:
            self.manual_target_temp = temperature

        if hvac_mode is not None:
            self.manual_hvac_mode = hvac_mode

        # Ensure to update state after changing the enslaved mode
        self.async_write_ha_state()

    async def async_restore_manual_state(self):
        """Restore manual state."""
        log.debug("async_restore_manual_state()")
        if self.manual_target_temp is not None:
            await self.async_set_temperature(temperature=self.manual_target_temp)

        if self.manual_hvac_mode is not None:
            await self.async_set_hvac_mode(self.manual_hvac_mode)


class FakeEnslavedGenericThermostat(EnslavedGenericThermostat):
    """
    Common class for fake thermostat that does not really control a real heater based on the state
    of a sensor, but have enslaved thermostat.
    Note: It current temperature is based on real enslaved thermostat.
    """

    _default_name = "Fake Thermostat"

    _enslaved_devices = []
    _enslaved_devices_temp = {}

    _target_temp = None
    _hvac_mode = None

    def __init__(self, **kwargs):
        """Initialize the thermostat."""
        super().__init__(**kwargs)

        self._enslaved_thermostats = kwargs["enslaved_thermostats"]
        log.debug(
            "%s %s managed thermostats: %s",
            self.__class__.__name__,
            kwargs["name"],
            ", ".join(self._enslaved_thermostats),
        )
        assert self._enslaved_thermostats, "No enslaved thermostat configured"

    #
    # Implement methods to allow saving and restore custom state attributes
    #

    async def async_added_to_hass(self) -> None:
        """
        Run when entity about to be added.

        Note: We can't call parent method because it register trigger on sensor/header entities, so
        do here all other things done and in particular, restore previous state or set initial state
        """

        # Retrieve and restore enslaved mode info from last known state
        await self.async_restore_last_extra_data()

        # Check If we have an old state
        if (old_state := await self.async_get_last_state()) is not None:
            # If we have no initial temperature, restore
            if self._target_temp is None:
                # If we have a previously saved temperature
                if old_state.attributes.get(ATTR_TEMPERATURE) is None:
                    if self.ac_mode:
                        self._target_temp = self.max_temp
                    else:
                        self._target_temp = self.min_temp
                    log.warning(
                        "Undefined target temperature, falling back to %s",
                        self._target_temp,
                    )
                else:
                    self._target_temp = float(old_state.attributes[ATTR_TEMPERATURE])
            if (
                self.preset_modes
                and old_state.attributes.get(ATTR_PRESET_MODE) in self.preset_modes
            ):
                self._attr_preset_mode = old_state.attributes.get(ATTR_PRESET_MODE)
            if not self._hvac_mode and old_state.state:
                self._hvac_mode = old_state.state

        else:
            # No previous state, try and restore defaults
            if self._target_temp is None:
                if self.ac_mode:
                    self._target_temp = self.max_temp
                else:
                    self._target_temp = self.min_temp
            log.warning("No previously saved temperature, setting to %s", self._target_temp)

        # Set default state to off
        if not self._hvac_mode:
            self._hvac_mode = HVACMode.OFF

        # Also add listener on enslaved thermostats to conpute master thermostat temperature
        log.debug(
            "Add listener on enslaved thermostats state changed (%s)",
            ", ".join(self._enslaved_thermostats),
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._enslaved_thermostats, self._async_enslaved_thermostat_changed
            )
        )

    #
    # Handle enslaved thermostats state changed event to retrieve their current temperature used
    # to compute master thermostat temperature. Only enslaved thermostat in auto enslaved mode are
    # used to compute the master thermostat.
    #

    async def _async_enslaved_thermostat_changed(
        self, event: EventType[EventStateChangedData]
    ) -> None:
        """Handle enslaved thermostat changes."""
        if "new_state" not in event.data:
            return
        entity_id = event.data["new_state"].entity_id
        is_handled = self._enslaved_thermostat_is_handled(event.data["new_state"])
        new_temp = event.data["new_state"].attributes.get(ATTR_CURRENT_TEMPERATURE)
        log.debug(
            "Enslaved thermostat %s state changed: temperature = %s, is handled = %s\n%s",
            entity_id,
            new_temp,
            is_handled,
            event,
        )
        if is_handled and new_temp is not None:
            self._enslaved_devices_temp[entity_id] = new_temp
        elif entity_id in self._enslaved_devices_temp:
            del self._enslaved_devices_temp[entity_id]
        self.async_write_ha_state()

    @staticmethod
    def _enslaved_thermostat_is_handled(state):
        """Check if the enslaved thermostat is handled based on its current state"""
        return True

    #
    # Compute current temperature from an average of enslaved thermostats current temperature
    #

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if not self._enslaved_devices_temp:
            log.debug(
                "No current temperature known for enslaved thermostats, "
                "can't compute master current temperature"
            )
            return None
        log.debug(
            "Compute current temperature from enslaved one (%s)",
            ", ".join([f"{cid}={temp}" for cid, temp in self._enslaved_devices_temp.items()]),
        )
        return sum(self._enslaved_devices_temp.values()) / len(self._enslaved_devices_temp)

    #
    # Override some methods GenericThermostat to make it a fake one (do not control any heater)
    #

    async def _async_control_heating(self, time=None, force=False):
        """Check if we need to turn heating on or off."""

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return None

    async def _async_heater_turn_on(self):
        """Turn heater toggleable device on."""

    async def _async_heater_turn_off(self):
        """Turn heater toggleable device off."""

    #
    # Implement methods to set enslaved mode state to control enslaved thermostats
    #

    async def async_set_enslaved_mode(self, **kwargs):
        """Set current enslaved mode."""
        log.debug("async_set_enslaved_mode(%s)", ", ".join([f"{k}={v}" for k, v in kwargs.items()]))
        if kwargs.get("mode"):
            await self._async_call_enslaved_thermostats_service(
                SERVICE_SET_ENSLAVED_MODE, {"mode": kwargs["mode"]}
            )
            if kwargs["mode"] == EnslavedMode.MANUAL:
                # If specified enslaved mode is manual, set enslaved thermostats temperature and
                # hvac_mode using specified parameters or current manual state
                if kwargs.get(ATTR_TEMPERATURE, self.manual_target_temp):
                    await self._async_call_enslaved_thermostats_service(
                        SERVICE_SET_TEMPERATURE,
                        {ATTR_TEMPERATURE: kwargs.get(ATTR_TEMPERATURE, self.manual_target_temp)},
                    )
                if kwargs.get(ATTR_HVAC_MODE, self.manual_hvac_mode):
                    await self._async_call_enslaved_thermostats_service(
                        SERVICE_SET_HVAC_MODE,
                        {ATTR_HVAC_MODE: kwargs.get(ATTR_HVAC_MODE, self.manual_hvac_mode)},
                    )
                return

        if ATTR_TEMPERATURE in kwargs:
            await self.async_set_temperature(**{ATTR_TEMPERATURE: kwargs[ATTR_TEMPERATURE]})
        if ATTR_HVAC_MODE in kwargs:
            await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])

    async def async_set_enslaved_target_temp(self, temperature):
        """Set current enslaved target temperature."""
        log.debug("async_set_enslaved_target_temp(%s)", temperature)
        await self.async_set_temperature(ATTR_TEMPERATURE=temperature)

    async def async_set_enslaved_hvac_mode(self, mode):
        """Set current enslaved HVAC mode."""
        log.debug("async_set_enslaved_hvac_mode(%s)", mode)
        await self.async_set_hvac_mode(mode)

    #
    # Implement methods to control scheduler mode on enslaved thermostats
    #

    async def async_start_scheduler_mode(self, temperature=None, hvac_mode=None):
        """Start scheduler mode on enslaved thermostats"""
        await self._async_call_enslaved_thermostats_service(
            SERVICE_START_SCHEDULER_MODE,
            {
                "temperature": temperature if temperature is not None else self.target_temperature,
                "hvac_mode": hvac_mode if hvac_mode is not None else self.hvac_mode,
            },
        )

    async def async_stop_scheduler_mode(self):
        """Stop scheduler mode on enslaved thermostats"""
        await self._async_call_enslaved_thermostats_service(SERVICE_STOP_SCHEDULER_MODE)

    #
    # Helpers methods
    #

    async def _async_call_enslaved_thermostats_service(self, service_name, service_data=None):
        """Set call service on enslaved thermostats."""
        service_data = service_data if service_data else {}
        for entity_id in self._enslaved_thermostats:
            try:
                service_data.update(entity_id=entity_id)
                await self.hass.services.async_call(
                    DOMAIN,
                    service_name,
                    service_data,
                )
            except HomeAssistantError:
                log.exception(
                    "Fail to call %s service on enslaved thermostat %s %s",
                    service_name,
                    entity_id,
                    f"with following data: {service_data}" if service_data else "without data",
                )


@dataclass
class EnslavedGenericThermostatExtraStoredData(ExtraStoredData):
    """Object to hold master thermostat extra stored data."""

    manual_target_temp: float | None = None
    manual_hvac_mode: HVACMode | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the text data."""
        return asdict(self)
