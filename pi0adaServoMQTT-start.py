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

def setup_logging(log_dir):
    # Create loggers
    main_logger = logging.getLogger(__name__)
    main_logger.setLevel(logging.INFO)
    log_file_format = logging.Formatter("[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(pathname)s:%(lineno)d")
    log_console_format = logging.Formatter("[%(levelname)s]: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_console_format)

    exp_file_handler = RotatingFileHandler('{}/exp_debug.log'.format(log_dir), maxBytes=10**6, backupCount=5) # 1MB file
    exp_file_handler.setLevel(logging.INFO)
    exp_file_handler.setFormatter(log_file_format)

    exp_errors_file_handler = RotatingFileHandler('{}/exp_error.log'.format(log_dir), maxBytes=10**6, backupCount=5)
    exp_errors_file_handler.setLevel(logging.WARNING)
    exp_errors_file_handler.setFormatter(log_file_format)

    main_logger.addHandler(console_handler)
    main_logger.addHandler(exp_file_handler)
    main_logger.addHandler(exp_errors_file_handler)
    return main_logger

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
    global newmsg, mqtt_servo_angle, mqtt_servoID, MQTT_REGEX
    logging.debug("Received: {0} with payload: {1}".format(msg.topic, str(msg.payload)))
    msgmatch = re.match(MQTT_REGEX, msg.topic)   # Check for match to subscribed topics
    if msgmatch:
        incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore"))) 
        incomingID = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(incomingD)] # breaks msg topic into groups - group/group1/group2
        if incomingID[1] == 'servoZCMD':
            mqtt_servoID = int(incomingID[2])
            mqtt_servo_angle = int(incomingD)

def on_publish(client, userdata, mid):
    """on publish will send data to broker"""
    #Debugging. Will unpack the dictionary and then the converted JSON payload
    logging.debug("msg ID: " + str(mid)) 
    logging.debug("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
    for key, value in mqtt_outgoingD.items():
        logging.debug("{0}:{1}".format(key, value))
    logging.debug("Converted msg published on topic: {0} with JSON payload: {1}\n".format(MQTT_PUB_TOPIC1, json.dumps(mqtt_outgoingD))) # Uncomment for debugging. Will print the JSON incoming msg
    pass 

def on_disconnect(client, userdata,rc=0):
    logging.debug("DisConnected result code "+str(rc))
    mqtt_client.loop_stop()

def mqtt_setup(IPaddress):
    global MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_PUB_TOPIC, SUBLVL1, MQTT_REGEX
    global mqtt_client, mqtt_outgoingD, device
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
    mqtt_outgoingD = {}            # Container for data to be published via mqtt
    device = []                    # mqtt lvl2 topic category and '.appended' in create functions

def create_servo(uaddress=0x40, uchannels=16):
    global MQTT_SUB_TOPIC, SUBLVL1, device, mqtt_outgoingD, mqtt_servoID, mqtt_servo_angle
    MQTT_SUB_TOPIC.append(SUBLVL1 + '/servoZCMD/+')
    device.append('servo')
    mqtt_outgoingD['servo'] = {}
    mqtt_outgoingD['servo']['send'] = False    # Servo does not send any data to nodered
    mqtt_servoID = 0
    mqtt_servo_angle = 90
    kit = ServoKit(address=uaddress, channels=uchannels)
    #channels=8 or 16, i2c=None, address=64 (0x40), reference_clock_speed=25000000, frequency=50) 50Hz = 20ms period
    setupinfo = True
    if setupinfo: print('Servo PCA9685 Kit Setup:{0}'.format(kit))
    return kit 

def main():
    global pinsummary
    global debugmqtt                          # Used for debugging mqtt messages
    global mqtt_servoID, mqtt_servo_angle     # Servo variables used in mqtt on_message
    global device, mqtt_outgoingD             # Containers setup in 'create' functions and used for Publishing mqtt
    global MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_CLIENT_ID, mqtt_client, MQTT_PUB_TOPIC

    #basicConfig root logger
    logging.basicConfig(level=logging.INFO)  # Change to DEBUG to see mqtt messages
    logging.info("Setup with basicConfig root logger")
    
    # MQTT structure: lvl1 = from-to     (ie Pi-2-NodeRed shortened to pi2nred)
    #                 lvl2 = device type (ie servoZCMD, stepperZCMD, adc)
    #                 lvl3 = free form   (ie controls, servo IDs, etc)
    MQTT_CLIENT_ID = 'pi' # Can make ID unique if multiple Pi's could be running similar devices (ie servos, ADC's) 
                          # Node red will need to be linked to unique MQTT_CLIENT_ID
    mqtt_setup('10.0.0.115')
    pca9685 = create_servo(0x40, 16)  # Pass the I2C address and number of channels (8 or 16)

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
        pca9685.servo[mqtt_servoID].angle = mqtt_servo_angle
 
if __name__ == "__main__":
    # Run main loop            
    main()