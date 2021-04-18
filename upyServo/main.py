from machine import Pin, ADC
import ujson

def on_message(topic, msg):
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
  client.set_callback(on_message)
  client.connect()
  client.subscribe(MQTT_SUB_TOPIC1)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (MQTT_SERVER, MQTT_SUB_TOPIC1))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  sleep(10)
  machine.reset()

try:
  mqtt_client = connect_and_subscribe()          # Connect and create the client
except OSError as e:
  restart_and_reconnect()

# MQTT setup is successful.
# Publish generic status confirmation easily seen on MQTT Explorer
# Initialize dictionaries and start the main loop.
mqtt_client.publish(b"status", b"esp32 connected, entering main loop")
pin = 2
led = Pin(pin, Pin.OUT) #2 is the internal LED
led.value(1)
sleep(1)
led.value(0)  # flash led to know main loop starting
outgoingD = {}
incomingD = {}
newmsg = True
while True:
    try:
      mqtt_client.check_msg()
      if newmsg:                              # INCOMING: New msg/instructions received
        for key, value in incomingD.items():
            direction = key
            duty = int(value)
            if direction == 'horiz':
                servoH.duty(duty)
            elif direction == 'vert':
                servoV.duty(duty)
            outgoingD[direction + 'i'] = duty
            mqtt_client.publish(MQTT_PUB_TOPIC1, ujson.dumps(outgoingD))
        newmsg = False
        #Uncomment prints for debugging. Will unpack the dictionary and then the converted JSON payload
        #print("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
        #for key, value in outgoingD.items():
        #    print("{0}:{1}".format(key, value))
        #print("Converted msg published on topic(tag): {0}".format(MQTT_PUB_TOPIC1))
        #print("JSON payload: {0}\n".format(ujson.dumps(outgoingD)))
    except OSError as e:
      restart_and_reconnect()