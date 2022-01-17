# HTU21D sensor driver for Home Assistant used in Raspberry Pi
Custom component HTU21D sensor for Home Assistant

Copy the content of this directory to your homeassistant config directory:
  - example: ./config/custom_components/dev_747_HTU21D/

##Requirements:
Enable I2C communication in Raspberry via raspi-config and install dependencies for handeling I2C communication in Python
```ruby
sudo apt-get update
sudo apt-get install pigpio python3-dev i2c-tools
pip3 install pigpio
```

##Parameters:
  - i2c_address: I2C address of HTU21D (typical 0x40)
  - i2c_bus_num: I2C bus number (default raspberry = 1)
  - name: custom name of the sensor
  - monitored_conditions: temperature, humidity

Exaple configuration.yaml file:
```ruby
sensor:
  - platform: dev747_HTU21D
    i2c_address: 0x40
    i2c_bus_num: 27
    name: "HTU21D_LIVING_ROOM"
    monitored_conditions:
      - temperature
      - humidity
    scan_interval: 5 
```
