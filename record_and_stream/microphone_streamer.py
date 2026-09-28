import time
import audio
from ulab import numpy as np
from ulab import utils

# -------- network + mqtt --------- #
import network
from mqtt import MQTTClient
# import paho.mqtt.client as mqtt

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

# mono audio
CHANNELS = 1
SIZE = 256 // (2 * CHANNELS)

# audio's raw buffer storage
raw_buf = None
audio.init(channels=CHANNELS, frequency=16000, gain_db=24, highpass=0.9883)

# ! APPLY QUEUE INTO THIS — CLEAR UP COMMENTARY
# the mic driver fills the buffer and calls this function.
# this is lacking a queue and might result in loss of data. the correct pattern needs to be:
# 1. copy the buffer
# 2. queue it
# 3. process it in order
# question: can this not result in audio laggy as fuck, from accumulated delays? answer: it can, but it's not too bad if low-latency is not a concern
def audio_callback(buf):
    # NOTE: do Not call any function that allocates memory.
    global raw_buf
    if raw_buf is None:
        raw_buf = buf


# start audio streaming. whenever we have a new chunk of data, the driver calls for audio_callback passing the buf param
# this call initializes this system and audio_callback as the handler function.
audio.start_streaming(audio_callback)

while True:
    if raw_buf is not None:
        # converts raw raw data to signed 2byte chunks
        pcm_buf = np.frombuffer(raw_buf, dtype=np.int16)
        payload = pcm_buf.tobytes()
        client.publish("openmv/raw-microphone-data", payload)
        print(payload)
        raw_buf = None

# Stop streaming
audio.stop_streaming()

# simply putting:
# we start streaming, and define the callback function. now, everytime the mic gets new data, it will call audio_callback
