[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

The component provide a Home Assistant integration that could be used to implement an enslaved thermostat. An enslaved thermostat is a generic thermostat with some additional properties, features and services.

## Installation

1. Click install.

## Configuration is done in the configuration.yaml file

As a regular [generic thermostat](https://www.home-assistant.io/integrations/generic_thermostat/), an enslaved thermostat is configured by adding some stuff in your `configuration.yaml` file. All supported parameters of a generic thermostat are supported and the `initial_enslaved_mode` parameter was had to control the initial enslaved mode (only used if no previous state is known).

__Basic configuration:__

```yaml
climate:
  - platform: enslaved_thermostat
    name: Kitchen
    heater: switch.kitchen_heater
    target_sensor: sensor.kitchen_temperature
```

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/brenard/hass-enslaved-thermostat.svg?style=for-the-badge
[commits]: https://github.com/brenard/hass-enslaved-thermostat/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/brenard/hass-enslaved-thermostat/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/brenard/hass-enslaved-thermostat.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40brenard-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/brenard/hass-enslaved-thermostat.svg?style=for-the-badge
[releases]: https://github.com/brenard/hass-enslaved-thermostat/releases
[user_profile]: https://github.com/brenard
