# this code connects to WiFi, then connects to the broker running on our machine at the selected topic.
# it publishes a confirmation message every 2.5 seconds.

# start and subscribe the broker to the topic of choice via the terminal running: mosquitto_sub -h localhost -t "openmv/test" -v

import time
import network
from mqtt import MQTTClient

SSID = "iphonesb"  # Network SSID
KEY = "localnetwork-key"  # Network key

# Init wlan module and connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

while not wlan.isconnected():
    print('Trying to connect to "{:s}"...'.format(SSID))
    time.sleep_ms(1000)

# We should have a valid IP now via DHCP
print("WiFi Connected ", wlan.ifconfig())

client = MQTTClient("openmv", "172.20.10.14", port=1883)
client.connect()

while True:
    client.publish("openmv/print", "connected")
    time.sleep_ms(2500)
