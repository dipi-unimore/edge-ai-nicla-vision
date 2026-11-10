import time 
import wave  # for writing .wav files
import threading 
import os  # for filesystem problms
import sys
from pathlib import Path
import paho.mqtt.client as mqtt

# saved in recordings/ at the repo root
OUTPUT_FILE_PATH = str(Path(__file__).resolve().parents[2] / 'recordings' / 'recording.wav')
MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'openmv/raw-microphone-data'
# how long the recording will be
RECORD_SECONDS = 5

# accumulates binary chunks
audio_chunks = []
# total received bytes (for logging)
total_bytes = 0
lock = threading.Lock()

# todo: internal publish + sub -> keep a q (also for the receiver)
# this allow for faster reading (and module the tC)
def on_message(client, userdata, msg):
    """Called when an MQTT message arrives. We append raw payload bytes."""
    global total_bytes
    # msg.payload is a raw binary payload
    with lock:
        audio_chunks.append(msg.payload)  # save this packet
        total_bytes += len(msg.payload)  # update byte counter
    print(f"received {len(msg.payload)} bytes (total: {total_bytes})")


# * ----- mqtt client code -----
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
# * --------------------------

# copy accumulated data under lock before processing to avoid races
# "with lock" locks this thread and exits it after processing inside finishes
with lock:
    chunks_copy = list(audio_chunks)  # shallow copy of the list of byte chunks
    total_bytes_copy = total_bytes

print(f"\ncollected {total_bytes_copy} total bytes")

if total_bytes_copy == 0:
    print("**NO DATA RECEIVED**")
    print("check >> is the board running? >> is the broker running on the correct port?")
else:
    # WAV file parameters (matching the producer file)
    output_file = OUTPUT_FILE_PATH
    sample_rate = 16000
    channels = 1
    sample_width = 2

    # join all binary chunks into a single bytes object ready to write
    audio_data = b''.join(chunks_copy)

    # PCM16 mono requires the total byte count to be divisible by (sample_width * channels)
    if len(audio_data) % (sample_width * channels) != 0:
        trim = len(audio_data) % (sample_width * channels)
        print(f"WARNING: payload not aligned to sample width, trimming {trim} trailing byte(s)")
        audio_data = audio_data[:-trim]


    # this is to ensure destination directory exists (avoids FileNotFoundError)
    out_dir = os.path.dirname(output_file)
    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            print(f"ERROR: cannot create output directory '{out_dir}': {e}")
            sys.exit(1)

    # writes the combined PCM data to a .wav file with friendly error handling
    try:
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(channels)        # mono
            wav_file.setsampwidth(sample_width)   # bytes per sample (2 = 16-bit)
            wav_file.setframerate(sample_rate)    # samples per second
            wav_file.writeframes(audio_data)      # raw PCM frames
    except FileNotFoundError:
        print(f"ERROR: output path '{output_file}' not found and could not be created.")
        print("Hint: check permissions or create the directory manually.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: failed to write WAV file '{output_file}': {e}")
        sys.exit(1)

    # logs
    duration = len(audio_data) / (sample_rate * channels * sample_width)
    print(f"Saved {output_file}")
    print(f"Duration: {duration:.2f}s")