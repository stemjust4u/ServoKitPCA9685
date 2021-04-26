from time import sleep
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from a deep sleep')

with open("stem", "rb") as f:
  stem = f.read().splitlines()

MQTT_SERVER = '10.0.0.115'
MQTT_USER = stem[0] 
MQTT_PASSWORD = stem[1] 
MQTT_SUB_TOPIC1 = b'esp32Cam1/servo'
MQTT_PUB_TOPIC1 = b'esp32Cam1/servo/status'
MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
WIFI_SSID = stem[2]
WIFI_PASSWORD = stem[3]

p5 = machine.Pin(19)
p4 = machine.Pin(21)
servoV = machine.PWM(p4,freq=50)
servoH = machine.PWM(p5,freq=50)
# initialize to neutral position
# 75 = 1.5mSec or neutral position
servoV.duty(75) 
servoH.duty(75)

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(WIFI_SSID, WIFI_PASSWORD)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())