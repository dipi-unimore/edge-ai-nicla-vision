import time
import csi
import time
import network
from mqtt import MQTTClient

# it's notorious how simpler the camera streamer is than the audio streamer, given the nature of continuous data present in both.

# -------- network + mqtt --------- #
SSID = "iphonesb"  # Network SSID
KEY = "localnetwork-key"  # Network key

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
# -------------------------------- #

# * camera setup
csi0 = csi.CSI()
csi0.reset()  # Reset and initialize the sensor.
csi0.pixformat(csi.RGB565)  # Set pixel format to RGB565 (or GRAYSCALE)
csi0.framesize(csi.QVGA)  # Set frame size to QVGA (320x240)
csi0.snapshot(time=2000)  # Wait for settings take effect.
clock = time.clock()

try:
    while True:
        clock.tick()
        img = csi0.snapshot()
        payload = bytes(img.compress(quality=50))  # compress and immediately extract bytes
        del img                                     # explicitly release the reference
        client.publish("openmv/raw-camera-data", payload)
except KeyboardInterrupt:
    pass
finally:
    client.disconnect()
