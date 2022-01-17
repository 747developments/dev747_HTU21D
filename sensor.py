from __future__ import annotations
"""Driver for Home Assistant to handle AM2320 sensor."""
import logging
import os
import time
import voluptuous as vol
import pigpio

from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.components.group import expand_entity_ids
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_BATTERY_LEVEL,
    CONF_DEVICES,
    CONF_TEMPERATURE_UNIT,
    CONF_NAME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
    CONF_SENSORS,
    CONF_MONITORED_CONDITIONS
)

from .const import (
    DEFAULT_NAME,
    SENSOR_TEMP,
    SENSOR_HUMID,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    CRC_VAL,
    _SENSOR_TYPES,    
    ADDR_HUMIDITY,
    ADDR_TEMPERATURE,
    ADDR_RESET,
    ADDR_WRITE_USER1,
    ADDR_READ_USER1,
    ADDR_USER1_VAL,
    HTU21D_HOLDMASTER,
    HTU21D_NOHOLDMASTER,
    HTU21D_A,
    HTU21D_B,
    HTU21D_C,
    _TEMP_RH_RES
)

CONF_I2C_ADDRESS        = "i2c_address"
CONF_I2C_BUS_NUM        = "i2c_bus_num"
CONF_NAME               = "name"

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.positive_int,
    vol.Required(CONF_I2C_BUS_NUM, default=DEFAULT_I2C_BUS): cv.positive_int,
    vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(_SENSOR_TYPES)]
        ),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""

    # if discovery_info is None:
        # return
    i2c_address = config.get(CONF_I2C_ADDRESS)
    i2c_bus_num = config.get(CONF_I2C_BUS_NUM)
    name = config.get(CONF_NAME)
    for monitored_condition in config[CONF_MONITORED_CONDITIONS]:
        async_add_entities([HTU21D(name, i2c_address, i2c_bus_num, monitored_condition)])
        time.sleep(0.001)

class HTU21D(SensorEntity):
    """ HTU21D."""

    def __init__(self, name, i2c_address, i2c_bus_num, monitored_condition):
        """Initialize the sensor."""
        self._monitored_condition = monitored_condition
        self._name = name
        self._state = None
        self.non_receive_counter = 0
        
        open_io="sudo pigpiod"
        try:
            os.system(open_io)
            time.sleep(0.1)
        except Exception as ex:
            _LOGGER.error("HTU21D: Exception during opening pigpio: %s" % (ex))
 
        self._i2c_bus_num = i2c_bus_num
        self._i2c_address = i2c_address 
        
        self.pi_bus = pigpio.pi()
        #self._i2c_bus = self.pi_bus.i2c_open(self._i2c_bus_num, self._i2c_address) # open i2c bus
        
        return
                
    def calc_crc16(self, remainder):
        """Calculate CRC."""
        divsor = 0x988000

        for i in range(0, 16):
            if( remainder & 1 << (23 - i) ):
                remainder ^= divsor

            divsor = divsor >> 1

        if remainder == 0:
            return True
        else:
            return False

    def combine_bytes(self, msb, lsb):
        """Combine bytes."""
        combined = ((msb << 8) | lsb)
        combined = combined & 0xFFFC
        return combined

    def soft_reset_sensor(self):
        """Soft-reset sensor."""
        try:
            handle = self.pi_bus.i2c_open(self._i2c_bus_num, self._i2c_address) # open i2c bus
            self.pi_bus.i2c_write_byte(handle, ADDR_RESET) 
            self.pi_bus.i2c_close(handle) 
            time.sleep(0.1)
        except Exception as ex:
            _LOGGER.error("HTU21D: Exception during soft-reset: %s" % (ex))
        return
            
    def get_temperature(self): 
        """Get temperature."""
        
        handle = self.pi_bus.i2c_open(self._i2c_bus_num, self._i2c_address)
        self.pi_bus.i2c_write_byte(handle, ADDR_TEMPERATURE)
        time.sleep(0.055)
        (count, byteArray) = self.pi_bus.i2c_read_device(handle, 3)
        self.pi_bus.i2c_close(handle) 
        
        t1 = byteArray[0]
        t2 = byteArray[1]
        t3 = byteArray[2]
   
        
        remainder = ( ( t1 << 8 ) + t2 ) << 8
        remainder |= t3
        crc_ret = self.calc_crc16(remainder)
        
        if not crc_ret:
            _LOGGER.error("HTU21D: BAD CRC Temperature")
            return(False)
        
        else:
            temperature = self.combine_bytes(t1, t2)
            return(self.compute_temperature(temperature))
            
        
    def compute_temperature(self, temperature):
        return(175.72 * (temperature / 2**16) - 46.85)
    
    def get_humidity(self):
        """Get temperature."""
        
        handle = self.pi_bus.i2c_open(self._i2c_bus_num, self._i2c_address)
        self.pi_bus.i2c_write_byte(handle, ADDR_HUMIDITY)
        time.sleep(0.055)
        (count, byteArray) = self.pi_bus.i2c_read_device(handle, 3)
        self.pi_bus.i2c_close(handle) 
        
        h1 = byteArray[0]
        h2 = byteArray[1]
        h3 = byteArray[2]
   
        remainder = ( ( h1 << 8 ) + h2 ) << 8
        remainder |= h3
        crc_ret = self.calc_crc16(remainder)
        
        if not crc_ret:
            _LOGGER.error("HTU21D: BAD CRC Humidity")
            return(False)
        
        else:
            humidity = self.combine_bytes(h1, h2)
            return(self.compute_humidity(humidity))
     
    def compute_humidity(self, humidity):
        return(125.0 * (humidity / 2**16) - 6.0)
        
    def get_data(self):
        """Get data from sensor."""
        self.soft_reset_sensor()        
        
        try:
            if self._monitored_condition == SENSOR_TEMP:
                self._state = self.get_temperature() 
            else:
                self._state = self.get_humidity()                
          
            if(self._state == False):
                self.non_receive_counter += 1
            else:
                self.non_receive_counter = 0
                self._state = round(self._state, 1)
               
        except Exception as ex:
            self.non_receive_counter += 1
            if(self.non_receive_counter >= 10):
                _LOGGER.error("Error retrieving HTU21 data %d - %s-%s: %s" % (self.non_receive_counter, self._name, self._monitored_condition, ex))
                self.non_receive_counter = 0
                self._state = None
            time.sleep(0.1)
       
    @property
    def name(self):
        """Return the name of the entity."""
        return "{} - {}".format(self._name, _SENSOR_TYPES[self._monitored_condition][0])
        
    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return _SENSOR_TYPES[self._monitored_condition][2]

    async def async_update(self):
        self.get_data()

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return _SENSOR_TYPES[self._monitored_condition][3]