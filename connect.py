# this code connects to a wifi and gets its IP. 
# this is dead code, left here to illustrate steps taken to build the project.

import network
import time

SSID = "iphonesb"  # Network SSID
KEY = "trash-AND-find4ble"  # Network key

# Init wlan module and connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

while not wlan.isconnected():
    print('Trying to connect to "{:s}"...'.format(SSID))
    time.sleep_ms(1000)

# We should have a valid IP now via DHCP
print("WiFi Connected ", wlan.ifconfig())
