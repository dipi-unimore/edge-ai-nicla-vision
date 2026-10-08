"""Keyword Spotting (KWS) using <TBD>
Captures audio and runs <libsname> keyword spotting.

Features:
- ...

Missing:
- Initializing and capturing audio;
- Running some form of inference using a library (probably librosa?)
- ...

USAGE:
source .venv/bin/activate
python3 intelligence/kws.py
"""

import paho.mqtt.client as mqtt
import json

mqttc = mqtt.Client(client_id="kws")
try:
    mqttc.connect("localhost", 1883, keepalive=60)
    mqttc.loop_start()
    print("connected to MQTT broker")
except Exception as e:
    print(f"could not connect to MQTT broker: {e}")

# mqttc.publish("openmv/yolov8n", json.dumps(detections))

def main():
    pass

if __name__ == '__main__':
    main()