#!/usr/bin/env python3

"""A MQTT client for RPI0
This script receives MQTT data
"""
from adafruit_servokit import ServoKit
from time import sleep
import sys, re
import re
from typing import NamedTuple

import paho.mqtt.client as mqtt

MQTT_ADDRESS = '10.0.0.115'
MQTT_USER = 'sj4u'
MQTT_PASSWORD = 'dewberry2233'
MQTT_TOPIC = 'pi0rojocam/servo/+'  # + means one or more occurrence
MQTT_REGEX = 'pi0rojocam/([^/]+)/([^/]+)'  #regular expression.  ^ means start with
MQTT_CLIENT_ID = 'pi0rojocam'

class ServoObj(NamedTuple):
    location: str
    device: str
    orientation: str
    value: float

kit = ServoKit(channels=16)
#kit.servo[1].set_pulse_width_range(750, 2250)

def valmap(value, istart, istop, ostart, ostop):
  return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

# create call back functions and then link them to the mqtt callback below in main program
def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))  #str() returns the nicely printable representation of a given object.
    client.subscribe(MQTT_TOPIC)

#on message will get the sensor data being published and write it to the influxdb
def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(msg.topic + ' ' + str(msg.payload))
    servoA = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8')) #set servoA to Class ServoObj return
    if servoA is not None:
        # perform action here when msg received
        if servoA.orientation == 'horz':
            kit.servo[0].angle = servoA.value
            sleep(0.1)
        elif servoA.orientation == 'vert':
            kit.servo[1].angle = servoA.value
            sleep(0.1)

def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEX, topic)      # check if topic matches the /+/+ format
    if match.group(1) == 'servo':
        location = match.group(0)
        device = match.group(1)
        orientation = match.group(2)
        if device == 'status':
            return None
        return ServoObj(location, device, orientation, int(payload))  # returns the data from Class ServoObj
    else:
        return None


#def _send_servoA_to_influxdb(servoA):  #servoA is the Class ServoObj
#    json_body = [
#        {
#            'measurement': servoA.measurement,  # measurement is similar to sql table. will have 2. one for temp and one for humidity
#            'tags': {
#                'location': servoA.location    #  tag name is 'location'. value is DHT11
#            },
#            'fields': {
#                'value': servoA.value           # field name is 'value'.  will store temp/humidity value
#            }
#        }
#    ]

def main():

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect  #bind call back function
    mqtt_client.on_message = on_message  #bind the function to be used when PUBLISH messages are found

    mqtt_client.connect(MQTT_ADDRESS, 1883)  # connect to the mqtt
    mqtt_client.loop_forever()            # loop forever and mqtt will call different functions based on the msg


if __name__ == '__main__':
    print('MQTT RPI0')
    main()
