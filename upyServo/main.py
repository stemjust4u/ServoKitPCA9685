from boot import MAIN_FILE_LOGGING, MAIN_FILE_MODE, MAIN_FILE_NAME, MAIN_FILE_OW, CPUFREQ, logfiles, rtc # Can remove for final code. Helps with python intellisense (syntax highlighting)
from timer import Timer, TimerFunc
from mytools import pcolor, rtcdate, localdate
import utime, uos, ubinascii, micropython, network, re, ujson, ulogging
from lib.umqttsimple import MQTTClient
from machine import Pin, ADC, PWM, RTC
import machine
import gc
gc.collect()
micropython.alloc_emergency_exception_buf(100)

if MAIN_FILE_LOGGING:
    with open(MAIN_FILE_NAME, MAIN_FILE_OW) as f:
        f.write("cpu freq: {0} GHz\n".format(CPUFREQ/10**9)) 
        f.write("All module debugging will write to file: {0} with mode: {1}\n".format(MAIN_FILE_NAME, MAIN_FILE_MODE))
        if machine.reset_cause() == machine.DEEPSLEEP_RESET:
            f.write('{0}, woke from a deep sleep'.format(utime.localtime()))
    print("All module debugging will write to file: {0} with mode: {1}\n".format(MAIN_FILE_NAME, MAIN_FILE_MODE))
    logfiles.append(MAIN_FILE_NAME)

# If wanting all modules to write to the same MAIN FILE then enable MAIN_FILE_LOGGING in boot.py
# If wanting modules to each write to individual files then make sure autoclose=True (safe with file open/close)
# If wanting a single module to quickly write to a log file then only enable one module and set autoclose=False
logger_log_level= 10
logger_type = "custom"  # 'basic' for basicConfig or 'custom' for custom logger
FileMode = 1 # If logger_type == 'custom'  then access to modes below
            #  FileMode == 1 # no log file
            #  FileMode == 2 # write to log file
logfile = __name__ + '.log'
if logger_type == 'basic': # Use basicConfig logger
    ulogging.basicConfig(level=logger_log_level) # Change logger global settings
    logger_main = ulogging.getLogger(__name__)
elif logger_type == 'custom' and FileMode == 1:        # Using custom logger
    logger_main = ulogging.getLogger(__name__)
    logger_main.setLevel(logger_log_level)
elif logger_type == 'custom' and FileMode == 2 and not MAIN_FILE_LOGGING: # Using custom logger with output to log file
    logger_main = ulogging.getLogger(__name__, logfile, mode='w', autoclose=True, filetime=5000)  # w/wb to over-write, a/ab to append, autoclose (with method), file time in ms to keep file open
    logger_main.setLevel(logger_log_level)
    logfiles.append(logfile)
elif logger_type == 'custom' and FileMode == 2 and MAIN_FILE_LOGGING:            # Using custom logger with output to main log file
    logger_main = ulogging.getLogger(__name__, MAIN_FILE_NAME, MAIN_FILE_MODE, 0)  # over ride with MAIN_FILE settings in boot.py
    logger_main.setLevel(logger_log_level)

logger_main.info('localtime: {0}'.format(localdate(utime.localtime())))
if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    logger_main.warning(',{0}, {1}Woke from a deep sleep{2}'.format(rtcdate(rtc.datetime()), pcolor.YELLOW, pcolor.ENDC))

def connect_wifi(WIFI_SSID, WIFI_PASSWORD):
    station = network.WLAN(network.STA_IF)

    station.active(True)
    station.connect(WIFI_SSID, WIFI_PASSWORD)

    while station.isconnected() == False:
        pass

    logger_main.info('Connection successful')
    logger_main.info(station.ifconfig())

def mqtt_setup(IPaddress):
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_REGEX, MQTT_PUB_TOPIC, SUBLVL1, ESPID
    with open("stem", "r") as f:    # Remove and over-ride MQTT/WIFI login info below
      stem = f.read().splitlines()
    MQTT_SERVER = IPaddress   # Over ride with MQTT/WIFI info
    MQTT_USER = stem[0]         
    MQTT_PASSWORD = stem[1]
    WIFI_SSID = stem[2]
    WIFI_PASSWORD = stem[3]
    connect_wifi(WIFI_SSID, WIFI_PASSWORD)
    MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
    MQTT_SUB_TOPIC = []
    SUBLVL1 = b'nred2' + ESPID  # Items that are sent as part of mqtt topic will be binary (b'item)
    MQTT_PUB_TOPIC = [ESPID + b'2nred', ESPID]
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
    logger_main.info('(CONNACK) Connected to {0} MQTT broker'.format(MQTT_SERVER))
    for topics in MQTT_SUB_TOPIC:
        client.subscribe(topics)
        logger_main.info('Subscribed to {0}'.format(topics)) 
    return client

def mqtt_on_message(topic, msg):
    global MQTT_REGEX, deviceD           # Standard variables for mqtt projects
    global mqtt_servo_duty, mqtt_servoID # Specific for servo
    logger_main.debug("Received topic(tag): {0} payload:{1}".format(topic, msg.decode("utf-8", "ignore")))
    msgmatch = re.match(MQTT_REGEX, topic)
    if msgmatch:
        mqtt_payload = ujson.loads(msg.decode("utf-8", "ignore")) # decode json data
        mqtt_topic = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(mqtt_payload)]
        if mqtt_topic[1] == b'servoZCMD':
            mqtt_servoID = int(mqtt_topic[2])
            deviceD['servoDuty'][mqtt_servoID] = int(mqtt_payload)  # Set the servo duty from mqtt payload

def mqtt_reset():
    logger_main.info('Failed to connect to MQTT broker. Reconnecting...')
    utime.sleep_ms(5000)
    machine.reset()


# umqttsimple requires topics to be byte (b') format. For string.join to work on topics, all items must be the same, bytes.
ESPID = b'esp'  # Specific MQTT_PUB_TOPICS created at time of publishing using string.join (specifically lvl2.join)
mqtt_setup('10.0.0.115')  # Setup mqtt variables (topics and data containers) used in on_message, main loop, and publishing

deviceD = {}       # Primary container for storing all topics and data

pinsummary = []

servo = []
servopins = [22, 23]
MQTT_SUB_TOPIC.append(SUBLVL1 + b'/servoZCMD/+') # Topic to monitor for new servo commands, duty, from mqtt nodered
mqtt_servoID = 0     # container for mqtt servo ID
mqtt_servo_duty = 0  # container for mqtt servo duty
freq=50       # higher freq has lower duty resolution. esp32 can go from 1-40000 (40MHz crystal oscillator) 
neutral = 75  # initialize to neutral position, 75=1.5mSec at 50Hz. (75/50=1.5ms or 1.5ms/20ms period = 7.5% duty cycle)
deviceD['servoDuty'] = []
for i, pin in enumerate(servopins):
    servo.append(PWM(Pin(pin),freq))
    servo[i].duty(neutral)
    deviceD['servoDuty'].append(neutral)
    pinsummary.append(pin)
logger_main.info('Servo:{0}'.format(servo))

logger_main.info('Pins in use:{0}'.format(sorted(pinsummary)))
#==========#
# Connect and create the client
try:
    mqtt_client = mqtt_connect_subscribe()
except OSError as e:
    mqtt_reset()
# MQTT setup is successful, publish status msg and flash on-board led
mqtt_client.publish(b'status'.join(MQTT_PUB_TOPIC), b'esp32 connected, entering main loop')
# Initialize flags and timers
on_msg_timer_ms = 100    # Frequency (ms) to check for msg
t0onmsg_ms = utime.ticks_ms()
checkmsgs = False

while True:
    try:
        if utime.ticks_diff(utime.ticks_ms(), t0onmsg_ms) > on_msg_timer_ms:
            checkmsgs = True
            t0onmsg_ms = utime.ticks_ms()
        
        if checkmsgs:
            mqtt_client.check_msg()
            checkmsgs = False
            
        servo[mqtt_servoID].duty(deviceD['servoDuty'][mqtt_servoID]) # Servo commands

    except OSError as e:
        mqtt_reset()
