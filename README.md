# Enslaved thermostat integration for Home Assistant

The repository provide a Home Assistant integration that could be used to implement an enslaved
thermostat. An enslaved thermostat is a generic thermostat with some additional properties, features
and services.

Three enslaved modes are supported:
- `auto`: the target temperature and the HVAC mode of the thermostat are set regarding current
  enslaved parameters. Any manual changes on the climate entity will put the thermostat in `manual`
  enslaved mode.
- `manual`: the thermostat works as a regular generic thermostat
- `off`: the thermostat is forced to OFF. No manual change on the climate entity is allowed (and
  triggered an error).

The enslaved mode could be control using on of the following climate entity services:

- `enslaved_thermostat.set_enslaved_mode`: set the enslaved mode and its parameters. Three
  parameters are accepted:

  - `mode`: the enslaved mode (required)
  - `temperature`: the target temperature when the thermostat is in enslaved auto mode (optional)
  - `hvac_mode`: the HVAC mode when the thermostat is in enslaved auto mode (optional)

- `enslaved_thermostat.set_enslaved_target_temperature`: set the target temperature when the
  thermostat is in enslaved auto mode. The temperature have to be specified with the `temperature`
  parameter.

- `enslaved_thermostat.set_enslaved_hvac_mode`: set the HVAC mode when the thermostat is in enslaved
  auto mode. The HVAC mode have to be specified with the `mode` parameter.

Enslaved thermostat also have a special scheduler mode controlled by the
`enslaved_thermostat.start_scheduler_mode` and `enslaved_thermostat.stop_scheduler_mode` entity
services. When putting the thermostat in scheduler mode, its current state is stored and it will be
restored when the thermostat leave the scheduler mode. Furthermore, no manual change is allowed when
then thermostat is in scheduler mode (and triggered an error). Changes on enslaved mode are allowed,
but not applied until the thermostat is in scheduler mode.

To put the thermostat in scheduler mode, you have to call the
`enslaved_thermostat.start_scheduler_mode` with the following parameters:

- `temperature`: the target temperature to set as long as the thermostat will be in scheduler mode
  (required)
- `hvac_mode`: the HVAC mode to set as long as the thermostat will be in scheduler mode (optional,
  default: `heat`)

To leave the scheduler mode, just call the `enslaved_thermostat.stop_scheduler_mode` without
parameter.

Finally, all custom parameters added to implement enslaved thermostat are exposed using some custom
state attributes:

- `enslaved_mode`: current enslaved mode
- `enslaved_target_temp`: current target temperature in enslaved auto mode
- `enslaved_hvac_mode`: current HVAC mode in enslaved auto mode
- `in_scheduler_mode`: this boolean specified is the thermostat is in the special scheduler mode
- `scheduler_previous_target_temp`: the target temperature of the thermostat before it entered in
  scheduler mode (`null` if not currently in scheduler mode)
- `scheduler_previous_hvac_mode`: the HVAC mode of the thermostat before it entered in scheduler
  mode (`null` if not currently in scheduler mode)

__Example of exposed state attributes:__

```yaml
hvac_modes:
  - heat
  - 'off'
min_temp: 7
max_temp: 35
target_temp_step: 0.1
current_temperature: 15
temperature: 22.5
hvac_action: 'off'
enslaved_mode: 'off'
enslaved_target_temp: 18
enslaved_hvac_mode: heat
in_scheduler_mode: false
scheduler_previous_target_temp: null
scheduler_previous_hvac_mode: null
friendly_name: Virtual thermostat
supported_features: 1
```

## Installation

### Using HACS

Add integration via HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=brenard&repository=hass-enslaved-thermostat&category=integration)

After, you can configure your enslaved thermostat as a regular [generic thermostat](https://www.home-assistant.io/integrations/generic_thermostat/)
with some additional parameters (see [Configuration](#configuration)).

### Manually

Put the `custom_components/enslaved_thermostat` directory in your Home Assistant `custom_components`
directory and restart Home Assistant. You can now add this integration (look for _"CCEI Tild"_) and provide the
IP address (or hostname) of your Tild box.

__Note:__ The `custom_components` directory is located in the same directory of the
`configuration.yaml`. If it doesn't exists, create it.

## Configuration

As a regular [generic thermostat](https://www.home-assistant.io/integrations/generic_thermostat/),
an enslaved thermostat is configured by adding some stuff in your `configuration.yaml` file. All
supported parameters of a generic thermostat are supported and the `initial_enslaved_mode` parameter
was had to control the initial enslaved mode (only used if no previous state is known).

__Basic configuration:__

```yaml
climate:
  - platform: enslaved_thermostat
    name: Kitchen
    heater: switch.kitchen_heater
    target_sensor: sensor.kitchen_temperature
```

## Run development environment

A development environment is provided with this integration if you want to contribute. The `manage`
script at the root of the repository permit to create and start a Home Assistant docker container
with a pre-installation of this integration (linked to sources).

Start by create the container by running the command `./manage create` and start it by running
`./manage start` command. You can now access to Home Assistant web interface on
[http://localhost:8123](http://localhost:8123) and follow the initialization process of the Home
Assistant instance.

A custom `configuration.yaml` is also provided to configure a virtual enslaved thermostat acting on
a virtual heater (in fact, an `input_boolean` entry) and follow if virtual sensor temperature (in
fact an `input_number` entry). This virtual thermostat is useful to test your changes and new
features.

__Details about the manage script usage:__

```
Usage: ./manage [command]
  Available commands:
    create                     Create docker container
    remove                     Remove docker container
    recreate                   Recreate docker container
    start                      Start docker container
    status                     Show docker container status
    stop                       Stop docker container
    restart                    Restart docker container
    check                      Check code using configured pre-commit hooks
    logs                       Show (and follow) docker container logs
    truncate-logs              Truncate docker container logs
    shell                      Start a shell in docker container context
```

## Debugging

To enable debug log, edit the `configuration.yaml` file and locate the `logger` block. If it does not
exists, add it with the following content :

```yaml
logger:
  default: warn
  logs:
    custom_components.enslaved_thermostat: debug
```

__Note:__

- debug logging is defaultly set to debug in the provided `configuration.yaml` file of the
development environment.
- In development environment and you will be able to follow docker container logs by running
the `./manage logs` command.
