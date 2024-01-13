# Enslaved thermostat integration for Home Assistant

The repository provide a Home Assistant integration that could be used to implement an enslaved
thermostat. An enslaved thermostat is a generic thermostat with some additional properties, features
and services.

Three enslaved modes are supported: auto, manual and off.

FIXME: add details on enslaved modes and services.

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

## Debugging

To enable debug log, edit the `configuration.yaml` file and locate the `logger` block. If it does not
exists, add it with the following content :

```yaml
logger:
  default: warn
  logs:
    custom_components.enslaved_thermostat: debug
```

Don't forget to restart Home Assistant after.

**Note:** In development environment and you will be able to follow docker container logs by running
the `./manage logs` command.
