import utime, ubinascii, micropython, network, re, ujson
from lib.umqttsimple import MQTTClient
from machine import Pin, PWM
import gc
gc.collect()
micropython.alloc_emergency_exception_buf(100)

def connect_wifi(WIFI_SSID, WIFI_PASSWORD):
    station = network.WLAN(network.STA_IF)

    station.active(True)
    station.connect(WIFI_SSID, WIFI_PASSWORD)

    while station.isconnected() == False:
        pass

    print('Connection successful')
    print(station.ifconfig())

def mqtt_setup(IPaddress):
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_REGEX
    with open("stem", "rb") as f:    # Remove and over-ride MQTT/WIFI login info below
      stem = f.read().splitlines()
    MQTT_SERVER = IPaddress   # Over ride with MQTT/WIFI info
    MQTT_USER = stem[0]         
    MQTT_PASSWORD = stem[1]
    WIFI_SSID = stem[2]
    WIFI_PASSWORD = stem[3]
    MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
    MQTT_SUB_TOPIC = []
    # Specific MQTT_SUB_TOPICS for ADC, servo, stepper are .appended below
    MQTT_REGEX = rb'nred2esp/([^/]+)/([^/]+)' # b'txt' is binary format. Required for umqttsimple to save memory
                                              # r'txt' is raw format for easier reg ex matching
                                              # 'nred2esp/+' would also work but would not return groups
                                              # () group capture. Useful for getting topic lvls in on_message
                                              # [^/] match a char except /. Needed to get topic lvl2, lvl3 groups
                                              # + will match one or more. Requiring at least 1 match forces a lvl1/lvl2/lvl3 topic structure
                                              # * could also be used for last group and then a lvl1/lvl2 topic would also be matched

def mqtt_connect_subscribe():
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_SUB_TOPIC, MQTT_USER, MQTT_PASSWORD
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PASSWORD)
    client.set_callback(mqtt_on_message)
    client.connect()
    print('(CONNACK) Connected to {0} MQTT broker'.format(MQTT_SERVER))
    for topics in MQTT_SUB_TOPIC:
        client.subscribe(topics)
        print('Subscribed to {0}'.format(topics)) 
    return client

def mqtt_on_message(topic, msg):
    global MQTT_REGEX, debugmqtt
    global mqtt_servo_duty, mqtt_servoID
    if debugmqtt: print("Received topic(tag): {0}".format(topic))
    msgmatch = re.match(MQTT_REGEX, topic)
    if msgmatch:
        incomingD = ujson.loads(msg.decode("utf-8", "ignore")) # decode json data
        incomingID = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(incomingD)]
        if incomingID[1] == b'servoZCMD':
            mqtt_servoID = int(incomingID[2])
            mqtt_servo_duty = int(incomingD)

def mqtt_reset():
    print('Failed to connect to MQTT broker. Reconnecting...')
    utime.sleep_ms(5000)
    machine.reset()

def create_servo(pinlist):
    global MQTT_SUB_TOPIC, device, outgoingD, mqtt_servoID, mqtt_servo_duty
    MQTT_SUB_TOPIC.append(b'nred2esp/servoZCMD/+')
    device.append(b'servo')
    outgoingD[b'servo'] = {}
    outgoingD[b'servo']['send'] = False    # Servo does not send any data to nodered
    mqtt_servoID = 0
    mqtt_servo_duty = 0
    servoArr = []
    setupinfo = True
    freq=50       # higher freq has lower duty resolution. esp32 can go from 1-40000 (40MHz crystal oscillator) 
    neutral = 75  # initialize to neutral position, 75=1.5mSec at 50Hz. (75/50=1.5ms or 1.5ms/20ms period = 7.5% duty cycle)
    for i, pin in enumerate(pinlist):
        servoArr.append(PWM(Pin(pin),freq))
        servoArr[i].duty(neutral)
        pinsummary.append(pin)
    if setupinfo: print('Servo:{0}'.format(servoArr))
    return servoArr 

def main():
    global pinsummary
    global debugmqtt                                  # Used for debugging mqtt messages
    global mqtt_servoID, mqtt_servo_duty     # Servo variables used in mqtt on_message
    global device, outgoingD                          # Containers setup in 'create' functions and used for Publishing mqtt
    
    #===== SETUP MQTT/DEBUG VARIABLES ============#
    # Setup mqtt variables (topics and data containers) used in on_message, main loop, and publishing
    # Further setup of variables is completed in specific 'create_device' functions
    mqtt_setup('10.0.0.115')
    device = []    # mqtt lvl2 topic category and '.appended' in create functions
    outgoingD = {} # container used for publishing mqtt data
    
    # umqttsimple requires topics to be byte format. For string.join to work on topics, all items must be the same, bytes.
    ESPID = b'/esp32A'  # Specific MQTT_PUB_TOPICS created at time of publishing using string.join (specifically lvl2.join)
    MQTT_PUB_TOPIC = [b'esp2nred/', ESPID]
  
    # Frequency (ms) to check for msg
    on_msg_timer_ms = 100
    
    debugmqtt = False        # Turn ON to print mqtt msg traffic.
    
    #=== SETUP DEVICES ===#
    # Boot fails if pin 12 is pulled high
    # Pins 34-39 are input only and do not have internal pull-up resistors. Good for ADC
    # Items that are sent as part of mqtt topic will be binary (b'item)
    pinsummary = []
    
    servopins = [22, 23]
    servo = create_servo(servopins)

    print('Pins in use:{0}'.format(sorted(pinsummary)))
    #==========#
    # Connect and create the client
    try:
        mqtt_client = mqtt_connect_subscribe()
    except OSError as e:
        mqtt_reset()
    # MQTT setup is successful, publish status msg and flash on-board led
    mqtt_client.publish(b'status'.join(MQTT_PUB_TOPIC), b'esp32 connected, entering main loop')
    # Initialize flags and timers
    checkmsgs = False
    t0onmsg_ms = utime.ticks_ms()
    
    while True:
        try:
            if utime.ticks_diff(utime.ticks_ms(), t0onmsg_ms) > on_msg_timer_ms:
                checkmsgs = True
                t0onmsg_ms = utime.ticks_ms()
            
            servo[mqtt_servoID].duty(mqtt_servo_duty) # Servo commands
            
            if checkmsgs:
                mqtt_client.check_msg()
                checkmsgs = False
                
        except OSError as e:
            mqtt_reset()

if __name__ == "__main__":
    # Run main loop            
    main()