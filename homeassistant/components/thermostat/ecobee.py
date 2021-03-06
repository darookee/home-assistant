"""
homeassistant.components.thermostat.ecobee
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ecobee Thermostat Component

This component adds support for Ecobee3 Wireless Thermostats.
You will need to setup developer access to your thermostat,
and create and API key on the ecobee website.

The first time you run this component you will see a configuration
component card in Home Assistant.  This card will contain a PIN code
that you will need to use to authorize access to your thermostat.  You
can do this at https://www.ecobee.com/consumerportal/index.html
Click My Apps, Add application, Enter Pin and click Authorize.

After authorizing the application click the button in the configuration
card.  Now your thermostat and sensors should shown in home-assistant.

You can use the optional hold_temp parameter to set whether or not holds
are set indefintely or until the next scheduled event.

ecobee:
  api_key: asdfasdfasdfasdfasdfaasdfasdfasdfasdf
  hold_temp: True

"""
import logging

from homeassistant.components import ecobee
from homeassistant.components.thermostat import (ThermostatDevice, STATE_COOL,
                                                 STATE_IDLE, STATE_HEAT)
from homeassistant.const import (TEMP_FAHRENHEIT, STATE_ON, STATE_OFF)

DEPENDENCIES = ['ecobee']

_LOGGER = logging.getLogger(__name__)

ECOBEE_CONFIG_FILE = 'ecobee.conf'
_CONFIGURING = {}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Setup Platform """
    if discovery_info is None:
        return
    data = ecobee.NETWORK
    hold_temp = discovery_info['hold_temp']
    _LOGGER.info(
        "Loading ecobee thermostat component with hold_temp set to %s",
        hold_temp)
    add_devices(Thermostat(data, index, hold_temp)
                for index in range(len(data.ecobee.thermostats)))


class Thermostat(ThermostatDevice):
    """ Thermostat class for Ecobee """

    def __init__(self, data, thermostat_index, hold_temp):
        self.data = data
        self.thermostat_index = thermostat_index
        self.thermostat = self.data.ecobee.get_thermostat(
            self.thermostat_index)
        self._name = self.thermostat['name']
        self._away = 'away' in self.thermostat['program']['currentClimateRef']
        self.hold_temp = hold_temp

    def update(self):
        self.data.update()
        self.thermostat = self.data.ecobee.get_thermostat(
            self.thermostat_index)

    @property
    def name(self):
        """ Returns the name of the Ecobee Thermostat. """
        return self.thermostat['name']

    @property
    def unit_of_measurement(self):
        """ Unit of measurement this thermostat expresses itself in. """
        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        return self.thermostat['runtime']['actualTemperature'] / 10

    @property
    def target_temperature(self):
        """ Returns the temperature we try to reach. """
        if self.hvac_mode == 'heat' or self.hvac_mode == 'auxHeatOnly':
            return self.target_temperature_low
        elif self.hvac_mode == 'cool':
            return self.target_temperature_high
        else:
            return (self.target_temperature_low +
                    self.target_temperature_high) / 2

    @property
    def target_temperature_low(self):
        """ Returns the lower bound temperature we try to reach. """
        return int(self.thermostat['runtime']['desiredHeat'] / 10)

    @property
    def target_temperature_high(self):
        """ Returns the upper bound temperature we try to reach. """
        return int(self.thermostat['runtime']['desiredCool'] / 10)

    @property
    def humidity(self):
        """ Returns the current humidity. """
        return self.thermostat['runtime']['actualHumidity']

    @property
    def desired_fan_mode(self):
        """ Returns the desired fan mode of operation. """
        return self.thermostat['runtime']['desiredFanMode']

    @property
    def fan(self):
        """ Returns the current fan state. """
        if 'fan' in self.thermostat['equipmentStatus']:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def operation(self):
        """ Returns current operation ie. heat, cool, idle """
        status = self.thermostat['equipmentStatus']
        if status == '':
            return STATE_IDLE
        elif 'Cool' in status:
            return STATE_COOL
        elif 'auxHeat' in status:
            return STATE_HEAT
        elif 'heatPump' in status:
            return STATE_HEAT
        else:
            return status

    @property
    def mode(self):
        """ Returns current mode ie. home, away, sleep """
        mode = self.thermostat['program']['currentClimateRef']
        self._away = 'away' in mode
        return mode

    @property
    def hvac_mode(self):
        """ Return current hvac mode ie. auto, auxHeatOnly, cool, heat, off """
        return self.thermostat['settings']['hvacMode']

    @property
    def device_state_attributes(self):
        """ Returns device specific state attributes. """
        # Move these to Thermostat Device and make them global
        return {
            "humidity": self.humidity,
            "fan": self.fan,
            "mode": self.mode,
            "hvac_mode": self.hvac_mode
        }

    @property
    def is_away_mode_on(self):
        """ Returns if away mode is on. """
        return self._away

    def turn_away_mode_on(self):
        """ Turns away on. """
        self._away = True
        if self.hold_temp:
            self.data.ecobee.set_climate_hold(self.thermostat_index,
                                              "away", "indefinite")
        else:
            self.data.ecobee.set_climate_hold(self.thermostat_index, "away")

    def turn_away_mode_off(self):
        """ Turns away off. """
        self._away = False
        self.data.ecobee.resume_program(self.thermostat_index)

    def set_temperature(self, temperature):
        """ Set new target temperature """
        temperature = int(temperature)
        low_temp = temperature - 1
        high_temp = temperature + 1
        if self.hold_temp:
            self.data.ecobee.set_hold_temp(self.thermostat_index, low_temp,
                                           high_temp, "indefinite")
        else:
            self.data.ecobee.set_hold_temp(self.thermostat_index, low_temp,
                                           high_temp)

    def set_hvac_mode(self, mode):
        """ Set HVAC mode (auto, auxHeatOnly, cool, heat, off) """
        self.data.ecobee.set_hvac_mode(self.thermostat_index, mode)

    # Home and Sleep mode aren't used in UI yet:

    # def turn_home_mode_on(self):
    #     """ Turns home mode on. """
    #     self._away = False
    #     self.data.ecobee.set_climate_hold(self.thermostat_index, "home")

    # def turn_home_mode_off(self):
    #     """ Turns home mode off. """
    #     self._away = False
    #     self.data.ecobee.resume_program(self.thermostat_index)

    # def turn_sleep_mode_on(self):
    #     """ Turns sleep mode on. """
    #     self._away = False
    #     self.data.ecobee.set_climate_hold(self.thermostat_index, "sleep")

    # def turn_sleep_mode_off(self):
    #     """ Turns sleep mode off. """
    #     self._away = False
    #     self.data.ecobee.resume_program(self.thermostat_index)
