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
MQTT_SUB_TOPIC1 = 'pi0rojocam/servo'
MQTT_PUB_TOPIC1 = 'pi0rojocam/servo/status'

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
        client.subscribe(MQTT_SUB_TOPIC1)      # Subscribe to topic
        print("Successful Connection: {0}".format(str(rc)))
        print("Subscribed to: {0}\n".format(MQTT_SUB_TOPIC1))
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
    """on message callback will receive messages from the server/broker. Must be subscribed to the topic in on_connect"""
    global newmsg, incomingD
    if msg.topic == MQTT_SUB_TOPIC1:
        incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore")))  # decode the json msg and convert to python dictionary
        newmsg = True
        #Uncomment prints for debugging. Will print the JSON incoming payload and unpack the converted dictionary
        #print("Receive: msg on subscribed topic: {0} with payload: {1}".format(msg.topic, str(msg.payload))) 
        #print("Incoming msg converted (JSON->Dictionary) and unpacking")
        #for key, value in incomingD.items():
        #    print("{0}:{1}".format(key, value))

def on_publish(client, userdata, mid):
    """on publish will send data to client"""
    #Uncomment prints for debugging. Will unpack the dictionary and then the converted JSON payload
    #print("msg ID: " + str(mid)) 
    #print("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
    #for key, value in outgoingD.items():
    #    print("{0}:{1}".format(key, value))
    #print("Converted msg published on topic: {0} with JSON payload: {1}\n".format(MQTT_PUB_TOPIC1, json.dumps(outgoingD))) # Uncomment for debugging. Will print the JSON incoming msg
    pass # DO NOT COMMENT OUT

def on_disconnect(client, userdata,rc=0):
    logging.debug("DisConnected result code "+str(rc))
    mqtt_client.loop_stop()

#==== start/bind mqtt functions ===========#
# Create a couple flags to handle a failed attempt at connecting. If user/password is wrong we want to stop the loop.
mqtt.Client.connected = False          # Flag for initial connection (different than mqtt.Client.is_connected)
mqtt.Client.failed_connection = False  # Flag for failed initial connection
# Create our mqtt_client object and bind/link to our callback functions
mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
mqtt_client.on_connect = on_connect    # Bind on connect
mqtt_client.on_message = on_message    # Bind on message
mqtt_client.on_publish = on_publish    # Bind on publish
print("Connecting to: {0}".format(MQTT_SERVER))
mqtt_client.connect(MQTT_SERVER, 1883) # Connect to mqtt broker. This is a blocking function. Script will stop while connecting.
mqtt_client.loop_start()               # Start monitoring loop as asynchronous. Starts a new thread and will process incoming/outgoing messages.
# Monitor if we're in process of connecting or if the connection failed
while not mqtt_client.connected and not mqtt_client.failed_connection:
    print("Waiting")
    sleep(1)
if mqtt_client.failed_connection:      # If connection failed then stop the loop and main program. Use the rc code to trouble shoot
    mqtt_client.loop_stop()
    sys.exit()

# MQTT setup is successful. Initialize dictionaries and start the main loop.
outgoingD = {}
incomingD = {}
newmsg = True
while True:
    if newmsg:                                 # INCOMING: New msg/instructions have been received
        for key, value in incomingD.items():
            direction = key
            angle = value
            if direction == 'horiz':
                kit.servo[0].angle = angle            # Drive servo on channel 0
                sleep(0.1)           
            elif direction == 'vert':
                kit.servo[1].angle = angle     # Drive servo on channel 1
                sleep(0.1)
            outgoingD[direction + 'i'] = angle                
            mqtt_client.publish(MQTT_PUB_TOPIC1, json.dumps(outgoingD))
        newmsg = False                                # Reset the new msg flag
