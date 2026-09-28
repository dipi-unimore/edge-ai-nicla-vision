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

audio.init(channels=CHANNELS, frequency=16000, gain_db=24, highpass=0.9883)

# simple ring queue implementation. "ring" because indices wrap around when they reach the end; so we overwrite the same spots over and over. simplistic queue.
QUEUE_CAPACITY = 2
queue_slots = [None] * QUEUE_CAPACITY  # preallocated slots
queue_head = 0
queue_tail = 0
queue_count = 0  # how many slots are filled
queue_dropped = 0  # diagnostic counter for dropped chunks when full

def queue_push(buf):
    """Push a buffer reference into the queue.
    Returns True if accepted, False if the queue was full (chunk dropped)."""
    global queue_head, queue_count, queue_dropped
    if queue_count < QUEUE_CAPACITY:
        queue_slots[queue_head] = buf
        # ? advance head to the next write index.
        # ? (head + 1) % CAPACITY wraps to 0 when reaching CAPACITY-1,
        # ? implementing the circular/ring behavior without resizing.
        queue_head = (queue_head + 1) % QUEUE_CAPACITY
        queue_count += 1
        return True
    else:
        # queue full: drop newest chunk and increment log counter
        queue_dropped += 1
        print("queue dropped!")
        return False


def queue_pop():
    """Pop the oldest buffer reference from the queue, or None if empty."""
    global queue_tail, queue_count
    if queue_count == 0:
        return None
    buf = queue_slots[queue_tail]
    queue_slots[queue_tail] = None
    # ? advance tail to the next read index; wrap-around logic as head.
    # ? tail tracks the oldest filled slot. after reading it we move tail
    # ? forward so the next pop reads the next-oldest slot.
    queue_tail = (queue_tail + 1) % QUEUE_CAPACITY
    queue_count -= 1
    return buf

# the mic driver fills the buffer and calls this function.
# this can result in small accumulated delays, but it's not a problem if low-latency is not a concern (our use-case). our queue fixes it anyhow.
def audio_callback(buf):
    # NOTE: do Not call any function that allocates memory.
    # push a reference into the queue. if the queue is full we drop the newest chunk and increment `queue_dropped` for logs
    queue_push(buf)

# start audio streaming. whenever we have a new chunk of data, the driver calls for audio_callback passing the buf param
# this call initializes this system and audio_callback as the handler function.
audio.start_streaming(audio_callback)

while True:
    # pop oldest available buffer and process it.
    buf = queue_pop()
    if buf is not None:
        # convert raw data (bytes-like) to int16 and publish
        pcm_buf = np.frombuffer(buf, dtype=np.int16)
        payload = pcm_buf.tobytes()
        client.publish("openmv/raw-microphone-data", payload)
        print(payload)

# Stop streaming
audio.stop_streaming()

# simply putting:
# we start streaming, and define the callback function. now, everytime the mic gets new data, it will call audio_callback
