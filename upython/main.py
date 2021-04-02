from machine import Pin, ADC
from time import time, sleep
import ujson

def sub_cb(topic, msg):
  #print("sub cd function %s %s %s" % (topic, msg, MQTT_SUB_TOPIC1))
  global newmsg, incomingD
  if topic == MQTT_SUB_TOPIC1:
    incomingD = ujson.loads(msg.decode("utf-8", "ignore")) # decode json data to dictionary
    newmsg = True
    #Uncomment prints for debugging. Will print the JSON incoming payload and unpack the converted dictionary
    #print("Received topic(tag): {0}".format(topic))
    #print("JSON payload: {0}".format(msg.decode("utf-8", "ignore")))
    #print("Unpacked dictionary (converted JSON>dictionary)")
    #for key, value in incomingD.items():
    #  print("{0}:{1}".format(key, value))

def connect_and_subscribe():
  global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_SUB_TOPIC1, MQTT_USER, MQTT_PASSWORD
  client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PASSWORD)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(MQTT_SUB_TOPIC1)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (MQTT_SERVER, MQTT_SUB_TOPIC1))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()          # Connect and create the client
except OSError as e:
  restart_and_reconnect()

# MQTT setup is successful.
# Publish generic status confirmation easily seen on MQTT Explorer
# Initialize dictionaries and start the main loop.
client.publish(b"status", b"esp32 connected, entering main loop")
pin = 2
led = Pin(pin, Pin.OUT) #2 is the internal LED
outgoingD = {}
incomingD = {}
incomingD["onoff"] = 0
newmsg = True
while True:
    try:
      client.check_msg()
      if newmsg:                              # INCOMING: New msg/instructions received
        if incomingD["onoff"] == 1:            
          led.value(1)                                    # Turn on LED (set it to 1)
          outgoingD[str(pin) + 'i'] = 1                   # The i tells node-red an integer is being sent. Will see the check in the node-red MQTT parse function.
        elif incomingD["onoff"] == 0:          
          led.value(0)                                    # Turn off LED (set it to 0)
          outgoingD[str(pin) + 'i'] = 0                   # The i tells node-red an integer is being sent. Will see the check in the node-red MQTT parse function.
        else:
          outgoingD[str(pin) + 'i'] = 99                  # Update LED status to 99 for unknown
                                              # OUTGOING: Convert python dictionary to json and publish
        client.publish(MQTT_PUB_TOPIC1, ujson.dumps(outgoingD))
        newmsg = False                                     # Reset newmsg flag
        #Uncomment prints for debugging. Will unpack the dictionary and then the converted JSON payload
        #print("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
        #for key, value in outgoingD.items():
        #    print("{0}:{1}".format(key, value))
        #print("Converted msg published on topic(tag): {0}".format(MQTT_PUB_TOPIC1))
        #print("JSON payload: {0}\n".format(ujson.dumps(outgoingD)))
      sleep(0.1)
    except OSError as e:
      restart_and_reconnect()