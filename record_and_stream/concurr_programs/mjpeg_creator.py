import time 
import wave  # for writing .wav files
import threading 
import os  # for filesystem problms
import sys
import paho.mqtt.client as mqtt

# ! change file format to save
OUTPUT_FILE_PATH = '/home/otaviosb/Desktop/arduino-nicla-vision-playground/record_and_stream/recordings/video_recording.mjpeg'

MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'openmv/raw-camera-data'
# how long the recording will be
RECORD_SECONDS = 5

# accumulates binary chunks
video_chunks = []
# total received bytes (for logging)
total_bytes = 0
lock = threading.Lock()


def on_message(client, userdata, msg):
    """Called when an MQTT message arrives. We append raw payload bytes."""
    global total_bytes
    # msg.payload is a raw binary payload
    with lock:
        video_chunks.append(msg.payload)  # save this packet
        total_bytes += len(msg.payload)  # update byte counter
    print(f"received {len(msg.payload)} bytes (total: {total_bytes})")


# ----- mqtt client code -----
client = mqtt.Client()
client.on_message = on_message
# connect to broker (synchronous network operation)
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
# starts network loop in background thread so callbacks run concurrently
client.loop_start()

client.subscribe(MQTT_TOPIC)
print(f"recording for {RECORD_SECONDS} seconds...")
time.sleep(RECORD_SECONDS)

# leave the loop
client.loop_stop()
client.disconnect()
# ----------

# copy accumulated data under lock before processing to avoid races
# "with lock" locks this thread and exits it after processing inside finishes
with lock:
    chunks_copy = list(video_chunks)  # shallow copy of the list of byte chunks
    total_bytes_copy = total_bytes

print(f"\ncollected {total_bytes_copy} total bytes")

if total_bytes_copy == 0:
    print("**NO DATA RECEIVED**")
    print("check >> is the board running? >> is the broker running on the correct port?")
else:
   with open(OUTPUT_FILE_PATH, "wb") as f:
    for chunk in chunks_copy:
            f.write(chunk)
    # ? how would we do these logs for simple raw mjpeg data?
    # duration = len(audio_data) / (sample_rate * channels * sample_width)
    # print(f"Saved {output_file}")
    # print(f"Duration: {duration:.2f}s")
