"""
USAGE:
source .venv/bin/activate
python3 mqtt_tester.py

different pattern with paho:
- initialize the client using mqtcc = mqtt.Client(<id - unique id for connections>)
- then, on main, define callbacks for on_connect and on_message
- inside on_connect, run a client.subscribe(<actual topic name>)
- inside on_message, do whatever you want with your message (we just print)
- finally run a client.connect(host, port, "keepalive=<int>" - dk what for)
- and right after a client.loop_start() followed by a while True inifinitely looping
    - this is necessary because loop_start() starts a background thread, but we must keep the main thread also alive
"""

import paho.mqtt.client as mqtt
import time

MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'openmv/yolov8n'

def on_connect(client, _, __, rc):
    if rc == 0:
        try:
            print(f"connected to {MQTT_HOST}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC)
            print(f"subscribed to {MQTT_TOPIC}")
        except Exception as e:
            print(f"error on subsrcibing: {e}")
    else:
        print(f"connection failed: code {rc}")

def on_message(_, __, msg):
    payload = msg.payload.decode('utf-8')
    print(f"message received: {payload}")

if __name__ == '__main__':
    client = mqtt.Client(client_id="mqtt_tester")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        # starts network loop in background thread so callbacks run concurrently
        client.loop_start()  
        print(f"listening for detections on {MQTT_TOPIC}...")
        # keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()