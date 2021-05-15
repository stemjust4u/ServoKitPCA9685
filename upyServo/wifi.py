import network

with open("stem", "rb") as f:
  stem = f.read().splitlines()

WIFI_SSID = stem[2]
WIFI_PASSWORD = stem[3]

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(WIFI_SSID, WIFI_PASSWORD)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())
