# this code connects to the broker and sends motion data to the broker at 100hz frequency.

# start and subscribe the broker to the topic of choice via the terminal running: mosquitto_sub -h localhost -t "openmv/test" -v

import time
from lsm6dsox import LSM6DSOX
from machine import Pin
from machine import SPI

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

lsm = LSM6DSOX(SPI(5), cs=Pin("PF6", Pin.OUT_PP, Pin.PULL_UP))

while True:
    accel = lsm.accel()
    gyro = lsm.gyro()

    # format as JSON
    payload = '{{"ax":{:.3f},"ay":{:.3f},"az":{:.3f},"gx":{:.3f},"gy":{:.3f},"gz":{:.3f}}}'.format(
        accel[0], accel[1], accel[2],
        gyro[0],  gyro[1],  gyro[2]
    )

    client.publish("openmv/imu", payload)
    time.sleep_ms(10)
