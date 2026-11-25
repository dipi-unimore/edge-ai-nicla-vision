# Development log

This document records how the project was built, step by step: what was tried, what was read, what worked, and what did not. It is written for anyone joining the project who wants to understand the history before changing code.

## 1. Getting started

How to set up a machine that can reproduce the work.

- **Hardware:** Arduino Nicla Vision, USB cable, PC with a webcam (optional)
- **Software:** Python environment ([see the README](../README.md#python-setup)), `arduino-cli` or the Arduino IDE, OpenMV IDE, Mosquitto (or access to an external broker)
- **Accounts and services:** CVAT account for labeling pictures, Edge Impulse account for creating an Object Detection pipeline (impulse).

## 2. References and documentation read

| Topic                   | Source                                                      | Used for                                          |
| ----------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| Nicla Vision board      | https://docs.arduino.cc/tutorials/nicla-vision/user-manual/ | Board fundamentals                                |
| Mosquitto Streaming     | https://mosquitto.org/documentation/                        | Streaming/receiving over a broker                 |
| Camera visiopn (OpenCV) | https://docs.opencv.org/5.0/                                | Camera usage/yoloV8n                              |
| Data labeling (CVAT)    | https://docs.cvat.ai/docs/                                  | Labeling objects in frames using CVAT             |
| Edge Impulse            | https://docs.edgeimpulse.com/                               | Creating tiny model for EdgeAI usage on the board |

## 3. Development steps

<!-- Describe each phase in order. For each one, note what was done, why, and what went wrong. -->

### 3.1 Connectivity (MQTT)

- **What was done:** Set up a Mosquitto broker and connected the board to it over MQTT. Tested with `mqtt_pub.py`, then sent motion sensor data from the board at about 100 Hz (`motion_send_via_broker.py`).
- **Key decisions:** Using Mosquitto, either running on the PC or as an external broker. Topics use the `openmv/` prefix (e.g. `openmv/imu`, `openmv/yolov8n`). Detections are sent as JSON, camera and microphone data as raw bytes.
- **Related:** [docs/connectivity.md](connectivity.md)

### 3.2 Sensors and streaming

- **What was done:** Wrote a camera streamer and a microphone streamer for the board. Wrote two receivers for the PC: `mjpeg_creator.py` saves 5 seconds of video as `.avi`, and `wav_creator.py` saves 5 seconds of audio as `.wav`.
- **Key decisions:** The board publishes raw data over MQTT and the PC does all the file writing. The microphone streamer uses a small ring queue (2 slots) and drops the newest chunk when it is full, instead of blocking.
- **Problems and fixes:** Audio is continuous data and harder to stream than camera frames (the camera streamer is simpler). Added the queue with a dropped-chunk flag, try/except blocks, and directory checks on the PC side.
- **Related:** [docs/streaming.md](streaming.md)

### 3.3 Desktop vision prototype (YOLOv8n)

- **What was done:** Recorded frames of blue and red caps, labeled them in CVAT, and fine-tuned YOLOv8n on the two classes. Added negative scenes (no caps) afterwards. Webcam demo in `yolo_detector.py`.
- **Key decisions:** We use YOLOv8n for its small size. The dataset is split by recording, not by frame, so near-identical frames don't leak into validation. Hue augmentation is off (`hsv_h=0`), since a hue shift can turn blue into red.
- **Problems and fixes:** The CVAT free tier exports labels without images, so labels were matched to frames by file name. The model will rarely still fire on fingers and orange backgrounds. The negatives cut false positives by about 16% at 0.25 confidence and 23% at 0.5, but did not remove them.
- **Related:** [docs/intelligence.md](intelligence.md)

### 3.4 On-board detection (FOMO)

- **What was done:** Trained a FOMO model in Edge Impulse on the same dataset, exported it as an Arduino library, and wrote the `board/fomo_live` firmware that runs inference on the board. Added `fomo_viewer.py` to draw boxes and centroids on the PC.
- **Key decisions:** FOMO instead of YOLO on the board, since it is built for microcontrollers. Results go over USB serial, not the network, so detection needs no network. The model takes 96 × 96 int8 input with a 0.5 threshold. The board also sends a half-size frame so the viewer can show the image.
- **Problems and fixes:** Red cap recall (84%) is lower than blue (94%), and only the centre 240 × 240 crop is seen. These are kept as known limitations in [board-fomo.md](board-fomo.md#limitations).
- **Related:** [docs/board-fomo.md](board-fomo.md)

### 3.5 Audio pipeline (paused)

- **What was done:** Recorded audio with sounddevice and plotted melspectrograms with librosa (`mel_spectrogram.py`). Started `kws.py` as a skeleton that connects to the MQTT broker and has an empty `main()`.
- **Where it stopped:** Audio capture and inference in `kws.py` are not written yet. The 10-word keyword spotting model is left open for development for now.
- **Related:** [docs/intelligence.md#audio](intelligence.md#audio), `host/audio/`

## 4. Decisions and lessons learned

- **MQTT with Mosquitto for all board-to-PC traffic.** Every stream can be watched from a terminal with `mosquitto_sub`.
- **YOLOv8n on the PC, FOMO on the board.** YOLOv8n is small enough for a desktop demo, but NOT for a board with little RAM as Nicla Vision. For that, FOMO is the better, albeit simpler, choice.
- **Split datasets by recording, not by frame.** Consecutive frames are almost identical, so a frame-level split would make the validation numbers look better than they are.
- **No hue augmentation.** A hue shift could turn a blue cap into a red one.
- **FOMO results over USB serial.** The board viewer works without a network, which keeps the on-board demo independent of Wi-Fi and the broker.
- **Keep intermediate code.** Earlier scripts stay in the repo as the research trail, so the process can be followed step by step.

## 5. Known issues and open work

- Audio pipeline was suggested as and extra but was ultimately paused (`host/audio/`). Still to do: capture audio in `kws.py`, choose the inference library (librosa or TensorFlow, both still open), train the 10-word model, and add its results to [intelligence.md](intelligence.md#audio). The `USAGE` line in `kws.py` still points to `intelligence/kws.py`, which is an old path.
- Board scripts hardcode the Wi-Fi settings and the broker address in every file, so they must be edited by hand for each network. This can be solved by a helper tool or a config file that is modified once for all the repo.
- Red cap recall on the board is 84%, which can be made better with a bigger dataset and more examples, and only centroids of objects are detected (FOMO design). End-to-end frame rate is not measured yet.
- YOLOv8n still gives false positives on fingers and orange backgrounds.
- `wav_creator.py` has a TODO to keep a queue for the receiver as well as the publisher.
- Open topic from the original plan: how the board should react dynamically to its own detections.

## 6. Notes for new contributors

- Start with the [README](../README.md) and the phase docs listed in the [Documentation](../README.md#documentation) table.
- Work on the `development` branch and merge into `main` when a phase is ready.
- Commit messages use short prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- To add a new doc, create it in `docs/`, start it with `[← Back to main README](../README.md)`, and add a row to the Documentation table in the README.
- Contacts: [Otávio Sbampato Andrade](https://github.com/otaviosbampato) (development) and [Marco Picone](https://github.com/piconem) (advisor).
