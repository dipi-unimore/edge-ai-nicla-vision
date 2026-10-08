import time
import threading
import cv2
import numpy as np
import paho.mqtt.client as mqtt

# save an .avi (container for mjpeg frames)
OUTPUT_FILE_PATH = '/home/otaviosb/Desktop/arduino-nicla-vision-playground/record_and_stream/recordings/video_recording.avi'

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
    decoded_frames = []
    target_size = None

    # decode each MQTT payload as one JPEG frame and normalize any size mismatch.
    for index, chunk in enumerate(chunks_copy, start=1):
        frame = cv2.imdecode(np.frombuffer(chunk, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            print(f"warning: skipped chunk {index} because it was not a valid JPEG frame")
            continue

        if target_size is None:
            target_size = (frame.shape[1], frame.shape[0])
        elif (frame.shape[1], frame.shape[0]) != target_size:
            frame = cv2.resize(frame, target_size)

        decoded_frames.append(frame)

    if not decoded_frames:
        print("**NO VALID FRAMES DECODED**")
    else:
        import os

        out_dir = os.path.dirname(OUTPUT_FILE_PATH)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        fps = max(1.0, len(decoded_frames) / RECORD_SECONDS)
        writer = cv2.VideoWriter(
            OUTPUT_FILE_PATH,
            cv2.VideoWriter_fourcc(*'MJPG'),
            fps,
            target_size,
        )

        if not writer.isOpened():
            print(f"ERROR: could not open video writer for '{OUTPUT_FILE_PATH}'")
        else:
            for frame in decoded_frames:
                writer.write(frame)
            writer.release()
            print(f"Saved {OUTPUT_FILE_PATH}")
            print(f"Frames written: {len(decoded_frames)}")
            print(f"FPS used: {fps:.2f}")
