#!/usr/bin/env python3

"""A MQTT client for RPI0
This script receives MQTT data
"""
from adafruit_servokit import ServoKit
from time import sleep
import sys, re, logging, json
from os import path
from pathlib import Path
from typing import NamedTuple
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.DEBUG)

class ServoObj(NamedTuple):
    location: str
    device: str
    orientation: str
    value: float

kit = ServoKit(channels=16)                   # Create servo kit object. Set channels to the number of servo channels on your kit.
                                              # PCA9685 has 16 channels

# Import mqtt and wifi info. Remove if hard coding in python file
home = str(Path.home())
with open(path.join(home, "stem"),"r") as f:
    stem = f.read().splitlines()

#=======   SETUP MQTT =================#
MQTT_SERVER = '10.0.0.115'                    # Replace with IP address of device running mqtt server/broker
MQTT_USER = stem[0]                           # Replace with your mqtt user ID
MQTT_PASSWORD = stem[1]                       # Replace with your mqtt password
MQTT_CLIENT_ID = 'pi0rojocam'
MQTT_SUB_TOPIC = 'pi0rojocam/servo/+'         # + means one or more occurrence
MQTT_REGEX = 'pi0rojocam/([^/]+)/([^/]+)'     #regular expression.  ^ means start with

#====== MQTT CALLBACK FUNCTIONS ==========#
# Each callback function needs to be 1) defined and 2) assigned/linked in main program below
# on_connect = Connect to the broker and subscribe to TOPICs
# on_disconnect = Stop the loop and log the reason code
# on_message = When a message is received get the contents and assign it to a python dictionary (must be subscribed to the TOPIC)
# on_publish = Send a message to the broker

def on_connect(client, userdata, flags, rc):
    """ on connect callback verifies a connection established and subscribe to TOPICs"""
    print("attempting on_connect")
    if rc==0:
        mqtt_client.connected = True          # If rc = 0 then successful connection
        client.subscribe(MQTT_SUB_TOPIC)      # Subscribe to topic
        print("Successful Connection: {0}".format(str(rc)))
        print("Subscribed to: {0}\n".format(MQTT_SUB_TOPIC))
    else:
        mqtt_client.failed_connection = True  # If rc != 0 then failed to connect. Set flag to stop mqtt loop
        print("Unsuccessful Connection - Code {0}".format(str(rc)))

    ''' Code descriptions
        0: Successful Connection
        1: Connection refused: Unacceptable protocol version
        2: Connection refused: Identifier rejected
        3: Connection refused: Server unavailable
        4: Connection refused: Bad user name or password
        5: Connection refused: Not authorized '''

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server. Using loop_forever so action is taken in on_message"""
    print(msg.topic + ' ' + str(msg.payload))
    servoA = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8')) #set servoA to Class ServoObj return
    if servoA is not None:
        # perform action here when msg received
        if servoA.orientation == 'horz':
            kit.servo[0].angle = servoA.value     # Drive servo on channel 0
            sleep(0.1)
        elif servoA.orientation == 'vert':
            kit.servo[1].angle = servoA.value     # Drive servo on channel 1
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

def on_publish(client, userdata, mid):
    """on publish will send data to broker"""
    pass  # DO NOT COMMENT OUT

#==== start/bind mqtt functions ===========#
# Create our mqtt_client object and bind/link to our callback functions
mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
mqtt_client.on_connect = on_connect    # Bind on connect
mqtt_client.on_message = on_message    # Bind on message
mqtt_client.on_publish = on_publish    # Bind on publish
print("Connecting to: {0}".format(MQTT_SERVER))
mqtt_client.connect(MQTT_SERVER, 1883) # Connect to mqtt broker. This is a blocking function. Script will stop while connecting.
mqtt_client.loop_forever()               # Blocking loop. Will keep running and looking for messages. Actions are handled in the on_message function

#MQTT setup. Monitor for messages




