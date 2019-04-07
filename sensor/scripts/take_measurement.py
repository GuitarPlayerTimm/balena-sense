#!/usr/local/bin/python

# This script detects for the presence of either a BME680 sensor on the I2C bus or a Sense HAT
# The BME680 includes sensors for temperature, humidity, pressure and gas content
# The Sense HAT does not have a gas sensor, and so air quality is approximated using temperature and humidity only.

import sys
import bme680
import time
from sense_hat import SenseHat
from influxdb import InfluxDBClient

# The sensor to get the readings from, 'unset' if no sensor is found.
readFrom = 'unset'

# First, check to see if there is a BME680 on the I2C Bus using the Primary Address
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    readFrom = 'bme680'
except IOError:
    print('BME680 not found on 0x76')

# Second, if readFrom is still 'unset', check to see if there's a BME680 on the I2C Bus using the Secondary Address
if readFrom == 'unset':
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
        readFrom = 'bme680'
    except IOError:
        print('BME680 not found on 0x77')

# Third, if readFrom is still 'unset', check to see if there's a Sense HAT
if readFrom == 'unset':
    try:
        sensor = SenseHat()
        readFrom = 'sense-hat'
    except:
        print('Sense HAT not found')

if readFrom == 'bme680':
    print('Using BME680 for readings')
    # Import the BME680 methods and initialize the BME680 burnin
    import bme680_air_quality
    bme680_air_quality.start_bme680(sensor)
    get_readings = bme680_air_quality.get_readings
elif readFrom == 'sense-hat':
    print('Using Sense HAT for readings (no gas measurements)')
    # Import the Sense HAT methods
    import sense_hat_air_quality
    get_readings = sense_hat_air_quality.get_readings
else:
    # If this is still unset, no sensors were found; quit!
    sys.exit()

# Create the database client, connected to the influxdb container, and select/create the database
influx_client = InfluxDBClient('influxdb', 8086, database='balena-sense')
influx_client.create_database('balena-sense')

while True:
    measurements = get_readings(sensor)
    influx_client.write_points(measurements)
    time.sleep(10)
