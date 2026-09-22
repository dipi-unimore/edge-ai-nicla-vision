import subprocess
import time
import wave
import threading

OUTPUT_FILE_PATH = '/home/otaviosb/Desktop/arduino-nicla-vision-playground/recording.wav'

# start mosquitto_sub process
proc = subprocess.Popen(
    ['mosquitto_sub', '-h', 'localhost', '-t', 'openmv/raw-microphone-data', '-v'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)

audio_chunks = []
total_bytes = 0
stop_recording = False

def read_stream():
    global total_bytes # this indicates this is the global var, not a new one
    while not stop_recording: # the function returns, which, in python, kills the thread.
        chunk = proc.stdout.read(1024)
        if chunk:
            audio_chunks.append(chunk)
            total_bytes += len(chunk)
            print(f"Received {len(chunk)} bytes (total: {total_bytes})")

# start reader thread passing read_stream as handler
reader_thread = threading.Thread(target=read_stream, daemon=True)
reader_thread.start()

# Record for 5 seconds
print("Recording for 5 seconds...")
time.sleep(5)

# Stop recording
stop_recording = True # makes the loop return, killing the thread
reader_thread.join(timeout=1) # gives a little time for the thread to die
proc.terminate()
proc.wait()

print(f"\nCollected {len(audio_chunks)} chunks, {total_bytes} total bytes")

if total_bytes == 0:
    print("**No data received**. Check:")
    print("1. Is audio_fft_1.py running on the board?")
    print("2. Is the broker running on localhost:1883?")
else:
    # Write to WAV file
    output_file = OUTPUT_FILE_PATH
    sample_rate = 16000
    channels = 1
    sample_width = 2

    audio_data = b''.join(audio_chunks)
    with wave.open(output_file, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)

    duration = total_bytes / (sample_rate * channels * sample_width)
    print(f"Saved {output_file}")
    print(f"Duration: {duration:.2f}s")