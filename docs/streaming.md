# Sensors and Streaming

[← Back to main README](../README.md)

The board comes equipped with a microphone and a camera. As a means to understand the connectivity and capabilities of those features, a streamer+recorder feature for both the microphone and camera was developed in the repo.

The files inside the **`board/streaming`** and **`host/receivers/`** folders are responsible for those features, and work according to the following sketch:

<p align="center">
    <img src="../assets/microphone_flow_light.png"/>
</p>

As can be seen by the sketch, the flow works via 2 concurrent programs. One of them runs from the board and aims to capture and send sensor data in real-time.
The other aims to capture such data through the broker connection and save that data into a playable file on the repo.

<!-- ! GIF: live camera stream from the board next to the saved .avi playing back -->

## Running the receivers

Both receivers need the board streaming and an MQTT broker running. Run them from the repo root.

```bash
python3 host/receivers/mjpeg_creator.py   # saves recordings/video_recording.avi
python3 host/receivers/wav_creator.py     # saves recordings/recording.wav
```

> [!IMPORTANT]
> Make sure the board is running `camera_streamer.py` (video) or `microphone_streamer.py` (audio) and publishing to the MQTT topic.
