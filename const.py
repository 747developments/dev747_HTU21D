"""CONSTANTS"""

DEFAULT_NAME            = "I2C Sensor"
SENSOR_TEMP             = "temperature"
SENSOR_HUMID            = "humidity"
DEFAULT_I2C_ADDRESS     = "0x40"
DEFAULT_I2C_BUS         = 1
CRC_VAL                 = 0

ADDR_HUMIDITY               = 0xF5
ADDR_TEMPERATURE            = 0xF3
ADDR_RESET                  = 0xFE
ADDR_WRITE_USER1            = 0xE6
ADDR_READ_USER1             = 0xE7
ADDR_USER1_VAL              = 0x3A

HTU21D_HOLDMASTER           = 0x00
HTU21D_NOHOLDMASTER         = 0x10

# HTU21D Constants for Dew Point calculation
HTU21D_A = 8.1332
HTU21D_B = 1762.39
HTU21D_C = 235.66

_TEMP_RH_RES = (0, 1, 128, 129)

_SENSOR_TYPES = {
    "temperature":  ("Temperature",     "",     "mdi:thermometer",      "°C"),
    "humidity":     ("Humidity",        "",     "mdi:water-percent",    "%"),
}