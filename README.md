# Edge AI on the Arduino Nicla Vision
> Audio and vision intelligence for IoT: MQTT connectivity, camera and microphone streaming, object detection (YOLOv8n) and keyword spotting, with the end goal of running the models directly on the board (TinyML).
<p align="center">
    <img height="80" alt="UNIMORE Logo" src="./assets/logo_bianco.svg"/>
    &emsp;&emsp;
    <img height="80" alt="DIPI Logo" src="./assets/dipi.png"/>
</p>

**Status:** desktop development phase (YOLOv8n object detection and a keyword-spotting model). Deployment to the board is the next phase.

## Table of Contents

- [Current status](#current-status)
- [Research path](#research-path)
  - [Connectivity](#connectivity)
  - [Sensors and streaming](#sensors-and-streaming)
  - [Intelligence](#intelligence)
  - [Board integration](#board-integration)
- [How to run the demos](#how-to-run-the-demos)
- [Authorship](#authorship)

## Current status

This repo currently contains:
- **basics** folder, containing steps taken to understand board's sensors and mqtt broker
- **record_and_stream** folder, containing functional streaming and recording flows of both camera and microphone
- **intelligence** folder, containing the development of machine vision (object detection) using OpenCV and YOLOv8n, and the development of audio recording and melspectrogram generation using sounddevice and librosa, alongside with the development of a keyword spotting (KWS) model for 10 different words.

<!-- TODO: reorganize folder structure -->

## Research path

<p align="center">
    <img height="500px" alt="Project's original sketch" src="./assets/sketch.jpeg"/>
</p>

The project's development has been split into 4 phases:
- [x] Connectivity
- [x] Boards sensors and streaming
- [x] Intelligence
    - [x] Object detection (YOLOv8n)
    - [ ] Keyword spotting model (tensorflow)
- [ ] Board integration

### Connectivity

The board comes equipped with an antenna, and can connect to Bluetooth and WiFi. For our project, we chose to use MQTT and the [*Mosquitto*](https://mosquitto.org/) broker to subscribe and publish messages.

The design of the communication architecture can be seen below.

<p align="center">
    <img src="./assets/mqtt.png"/>
</p>

#### MQTT setup

##### Local broker

As seen in our repo's *mqtt_pub.py* code, the broker may run on the same machine as the board, where it can subscribe to any topic of choice. This can be done running ``mosquitto_sub -h localhost -t "<topic-name>" -v`` on a terminal, and, in your code, connecting to your machine's local ip address.

##### External broker

To connect to a broker already running in a different machine, you'd connect to their local IP address (if the board and the machine are on the same WiFi), or you'd connect to their public IP or domain (if they are running on different connections), as can be seen on the example below.

> ``client = MQTTClient("openmv", "broker.university.edu", port=1883)``  
> ``client.connect()``

### Sensors and streaming

The board comes equipped with a microphone and a camera. As a means to understand the connectivity and capabilities of those features, a streamer+recorder feature for both the microphone and camera was developed in the repo.

The files inside the **"record_and_stream"** folder are responsible for those features, and work according to the following sketch:

<p align="center">
    <img src="./assets/microphone_flow_light.png"/>
</p>

As can be seen by the sketch, the flow works via 2 concurrent programs. One of them runs from the board and aims to capture and send sensor data in real-time.
The other aims to capture such data through the broker connection and save that data into a playable file on the repo.

### Intelligence
The development of intelligence in the project is split into 2 main different phases. A development phase on a desktop machine using YOLOv8n/openCV for video and librosa/tensorflow for audio, and an integration phase into the board using TinyML[^1]

[^1]: This has yet to be confirmed.

#### Video
Video intelligence on the machine has been developed using openCV, an open-source library for real-time computer vision and image processing. The model used was YOLOv8n, specifically chosen for its small size and interesting didactic value.

The demo *yolo_detector.py* can be seen inside the intelligence folder and it describes the implementation of object detection and classification with bounding boxes, labels and confidence scores over the YOLOv8n model.

#### Audio
Audio intelligence on the machine is currently undergoing development.

As of now, audio recording and melspectrogram plotting has been implemented and can be seen described on the script *mel_spectrogram.py*, inside the intelligence folder. The libs used were sounddevice for audio recording and librosa for melspectrogram plotting.

### Board integration
> In the future!

## How to run the demos

1. **Initialize the virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### `yolo_detector.py`

Captures video from your webcam and runs YOLOv8n object detection on each frame, drawing bounding boxes around detected objects.

```bash
python3 intelligence/yolo_detector.py
```

### `mel_spectrogram.py`

Records audio from your device and plots a melspectrogram based on the acquired audio.

```bash
python3 intelligence/mel_spectrogram.py
```

### `mjpeg_creator.py`

Receives video frames via MQTT from the Nicla Vision board and saves them as an AVI video file. Requires an active MQTT broker and a board streaming camera data.

> [!IMPORTANT]
> Make sure the board is running `camera_streamer.py` and publishing video frames to the MQTT topic.

```bash
python3 record_and_stream/concurr_programs/mjpeg_creator.py
```

The recorded video will be saved to `record_and_stream/recordings/video_recording.avi`.

### `wav_creator.py`

Receives audio data via MQTT from the Nicla Vision board and saves it as a WAV audio file. Requires an active MQTT broker and a board streaming audio data.

> [!IMPORTANT]
> Make sure the board is running `microphone_streamer.py` and publishing audio data to the MQTT topic.


```bash
python3 record_and_stream/concurr_programs/wav_creator.py
```

The recorded audio will be saved to `record_and_stream/recordings/recording.wav`.

## Authorship
* Development: [Otávio Sbampato Andrade](https://github.com/otaviosbampato)
* Advisor: [Marco Picone](https://github.com/piconem)