import time
import csi
import time
from ulab import numpy as np
import network
from mqtt import MQTTClient

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

# * simple ring queue implementation. indices wrap around when they reach the end, so we overwrite the same spots over and over.
QUEUE_CAPACITY = 2
queue_slots = [None] * QUEUE_CAPACITY  # preallocated slots
queue_head = 0
queue_tail = 0
queue_count = 0  # how many slots are filled
queue_dropped = 0  # counter used for logs (unused rn)

# * camera setup
csi0 = csi.CSI()
csi0.reset()  # Reset and initialize the sensor.
csi0.pixformat(csi.RGB565)  # Set pixel format to RGB565 (or GRAYSCALE)
csi0.framesize(csi.QVGA)  # Set frame size to QVGA (320x240)
csi0.snapshot(time=2000)  # Wait for settings take effect.
clock = time.clock()

def queue_push(buf):
    """Push a buffer reference into the queue.
    Returns True if accepted, False if the queue was full (chunk dropped)."""
    global queue_head, queue_count, queue_dropped
    if queue_count < QUEUE_CAPACITY:
        queue_slots[queue_head] = buf
        # advance head to the next write index. circular/ring behavior without resizing.
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
    # tail tracks the oldest filled slot. after reading it we move tail forward so the next pop reads the next-oldest slot.
    queue_tail = (queue_tail + 1) % QUEUE_CAPACITY
    queue_count -= 1
    return buf


# ? what to do with code below? we currently "stream" via while True. do we NEED a video_streamer callback?
# # the mic driver fills the buffer and calls this function.
# def audio_callback(buf):
#     # NOTE: do Not call any function that allocates memory.
#     # push a reference into the queue
#     queue_push(buf)

# # start audio streaming. whenever we have a new chunk of data, the driver calls for audio_callback passing the buf param
# # this call initializes this system and audio_callback as the handler function.
# audio.start_streaming(audio_callback)

try:
    while True:
        # pop oldest available buffer and process it.
        # ! do we need a video_streamer_handler for the usage of the queue?
        # buf = queue_pop()
        # if buf is not None:
        clock.tick()
        img = csi0.snapshot()
        payload = bytes(img.compress(quality=50))  # compress and immediately extract bytes
        del img                                     # explicitly release the reference
        client.publish("openmv/raw-camera-data", payload)
except KeyboardInterrupt:
    pass
finally:
    # audio.stop_streaming()
    client.disconnect()
