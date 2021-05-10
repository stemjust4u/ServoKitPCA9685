#!/usr/bin/env python3

"""
PCA9685 Servo using adafruit servokit
Servo position received via mqtt from a node-red server

See HARDWARE/MQTT for TOPICS
"""
from adafruit_servokit import ServoKit
from time import sleep
import sys, re, logging, json
from os import path
from pathlib import Path
import paho.mqtt.client as mqtt 

def on_connect(client, userdata, flags, rc):
    """ on connect callback verifies a connection established and subscribe to TOPICs"""
    logging.info("attempting on_connect")
    if rc==0:
        mqtt_client.connected = True
        for topic in MQTT_SUB_TOPIC:
            client.subscribe(topic)
            logging.info("Subscribed to: {0}\n".format(topic))
        logging.info("Successful Connection: {0}".format(str(rc)))
    else:
        mqtt_client.failed_connection = True  # If rc != 0 then failed to connect. Set flag to stop mqtt loop
        logging.info("Unsuccessful Connection - Code {0}".format(str(rc)))

def on_message(client, userdata, msg):
    """on message callback will receive messages from the server/broker. Must be subscribed to the topic in on_connect"""
    global deviceD, MQTT_REGEX
    global mqtt_servoID, mqtt_servoAngle
    logging.debug("Received: {0} with payload: {1}".format(msg.topic, str(msg.payload)))
    msgmatch = re.match(MQTT_REGEX, msg.topic)   # Check for match to subscribed topics
    if msgmatch:
        mqtt_payload = json.loads(str(msg.payload.decode("utf-8", "ignore"))) 
        mqtt_topic = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(mqtt_payload)] # breaks msg topic into groups - group/group1/group2
        if mqtt_topic[1] == 'servoZCMD':
            mqtt_servoID = int(mqtt_topic[2])
            mqtt_servoAngle = int(mqtt_payload)  # Set the servo angle from mqtt payload

def on_publish(client, userdata, mid):
    """on publish will send data to broker"""
    logging.debug("msg ID: " + str(mid)) 
    pass 

def on_disconnect(client, userdata,rc=0):
    logging.debug("DisConnected result code "+str(rc))
    mqtt_client.loop_stop()

def mqtt_setup(IPaddress):
    global MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_PUB_TOPIC, SUBLVL1, MQTT_REGEX
    global mqtt_client
    home = str(Path.home())                       # Import mqtt and wifi info. Remove if hard coding in python script
    with open(path.join(home, "stem"),"r") as f:
        user_info = f.read().splitlines()
    MQTT_SERVER = IPaddress                    # Replace with IP address of device running mqtt server/broker
    MQTT_USER = user_info[0]                   # Replace with your mqtt user ID
    MQTT_PASSWORD = user_info[1]               # Replace with your mqtt password
    MQTT_SUB_TOPIC = []
    SUBLVL1 = 'nred2' + MQTT_CLIENT_ID
    # lvl2: Specific MQTT_PUB_TOPICS created at time of publishing done using string.join (specifically item.join)
    MQTT_PUB_TOPIC = [MQTT_CLIENT_ID + '2nred', MQTT_CLIENT_ID]
    MQTT_REGEX = SUBLVL1 + '/([^/]+)/([^/]+)' # 'nred2pi/+' would also work but would not return groups
                                              # () group capture. Useful for getting topic lvls in on_message
                                              # [^/] match a char except /. Needed to get topic lvl2, lvl3 groups
                                              # + will match one or more. Requiring at least 1 match forces a lvl1/lvl2/lvl3 topic structure
                                              # * could also be used for last group and then a lvl1/lvl2 topic would also be matched

def main():
    global mqtt_servoID, mqtt_servoAngle  # Servo variables
    global deviceD  # Main dictionary that holds information on devices setup
    global MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_CLIENT_ID, mqtt_client, MQTT_PUB_TOPIC

    #basicConfig root logger
    logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG to see mqtt messages
    logging.info("Setup with basicConfig root logger")
    
    # MQTT structure: lvl1 = from-to     (ie Pi-2-NodeRed shortened to pi2nred)
    #                 lvl2 = device type (ie servoZCMD, stepperZCMD, adc)
    #                 lvl3 = free form   (ie controls, servo IDs, etc)
    MQTT_CLIENT_ID = 'pi' # Can make ID unique if multiple Pi's could be running similar devices (ie servos, ADC's) 
                          # Node red will need to be linked to unique MQTT_CLIENT_ID
    mqtt_setup('10.0.0.115')

    deviceD = {}       # Primary container for storing all topics and data

    servoID, mqtt_servoID = 0, 0   # Initialize. Updated in mqtt on_message
    numservos = 16     # Number of servo channels to pass to ServoKit. Must be 8 or 16.
    i2caddr = 0x40     # I2C address on PCA9685 board
    mqtt_servoAngle = 90
    deviceD['servoAngle'] = [90]*numservos   # Initialize at 90°
    MQTT_SUB_TOPIC.append(f"{SUBLVL1}/servoZCMD/+")
                      # Other arguments reference_clock_speed=25000000, frequency=50) 50Hz = 20ms period
    pca9685 = ServoKit(address=i2caddr, channels=numservos)  
    logging.info(('Servo PCA9685 Kit on address:{0} {1}'.format(i2caddr, pca9685)))

    #==== START/BIND MQTT FUNCTIONS ====#
    #Create a couple flags to handle a failed attempt at connecting. If user/password is wrong we want to stop the loop.
    mqtt.Client.connected = False          # Flag for initial connection (different than mqtt.Client.is_connected)
    mqtt.Client.failed_connection = False  # Flag for failed initial connection
    # Create our mqtt_client object and bind/link to our callback functions
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
    mqtt_client.on_connect = on_connect        # Bind on connect
    mqtt_client.on_disconnect = on_disconnect  # Bind on disconnect    
    mqtt_client.on_message = on_message        # Bind on message
    mqtt_client.on_publish = on_publish        # Bind on publish
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

    # MAIN LOOP
    while True:
        servoID = mqtt_servoID                                      # Servo commands coming from mqtt
        deviceD['servoAngle'][servoID] = mqtt_servoAngle            # But could change data source from something other than mqtt
        pca9685.servo[servoID].angle = deviceD['servoAngle'][servoID] # Set the servo angle from mqtt
 
if __name__ == "__main__":
    # Run main loop            
    main()