# On-board FOMO detection

[← Back to main README](../README.md)

The FOMO model runs on the Nicla Vision itself. The board takes each camera frame, detects blue and red caps, and sends the results to a PC over USB. No network or cloud is needed for detection.

The sketch is [board/fomo_live/fomo_live.ino](../board/fomo_live/fomo_live.ino). The PC window is [host/vision/fomo_viewer.py](../host/vision/fomo_viewer.py).

<!-- 📸 GIF: fomo_viewer window showing boxes and centroids from the board, recorded with a screen recorder -->

## What runs where

- **Board:** camera capture, model inference (about 87 ms per frame), packing the results and a half-size frame.
- **PC:** reading the USB stream, drawing boxes and centroids, showing the window.

Per frame, the board sends:

| Part       | Size                          | Content                                             |
| ---------- | ----------------------------- | --------------------------------------------------- |
| Header     | 4 + 1 + 2 bytes               | Magic marker, number of detections, inference time  |
| Detections | 6 bytes each (up to 16)       | Class (0 blue, 1 red), confidence, box x, y, w, h   |
| Frame      | 160 × 120 × 2 bytes (RGB565)  | Camera frame at half resolution                     |

The PC looks for the magic marker to find the start of each packet, so it recovers if bytes are lost.

## The model

- **Type:** FOMO (Faster Objects, More Objects). It outputs one centroid per grid cell, not a full box.
- **Classes:** `blue_cap`, `red_cap`.
- **Input:** 96 × 96 RGB, from the centered 240 × 240 crop of the camera frame.
- **Quantization:** int8.
- **Detection threshold:** 0.5, set in the Edge Impulse library.

Validation results from the Edge Impulse evaluation (int8):

| Metric               | Value                 |
| -------------------- | --------------------- |
| F1 (caps, non-background) | 0.92             |
| Blue cap recall      | 94% (33 of 35)        |
| Red cap recall       | 84% (26 of 31)        |
| False positives on background | 1 blue, 2 red |

The metrics are in [assets/](../assets/ei-nicla-vision-caps-detection-object-detection-model-evaluation-metrics-json-file-model.9.json).

## Run it

Needs the Nicla Vision on USB, [arduino-cli](https://arduino.github.io/arduino-cli/) (or the Arduino IDE), and the Edge Impulse Arduino library for this model. Export the library from Edge Impulse (Deployment → Arduino library) and install the zip in the Arduino IDE (Sketch → Include Library → Add .ZIP Library).

1. **Flash the sketch.** This replaces the Edge Impulse firmware on the board.

   ```bash
   arduino-cli compile --fqbn arduino:mbed_nicla:nicla_vision board/fomo_live
   arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:mbed_nicla:nicla_vision board/fomo_live
   ```

2. **Start the viewer.** Install the Python packages from [README](../README.md#python-setup) first.

   ```bash
   python3 host/vision/fomo_viewer.py --port /dev/ttyACM0
   ```

   Press `q` in the window to quit. The window shows the frame at 4× size, a box and centroid for each cap, the confidence, and the inference time.

To restore the original Edge Impulse firmware, run `flash_linux.sh` (or the Windows or Mac script) in `models/nicla-vision-caps-detection-nicla-vision-v1-impulse-#1/`.

## Limitations

- **Only the center of the frame is detected.** The model sees the 240 × 240 crop in the middle of the 320 × 240 camera frame. Caps near the left or right edge are not seen.
- **Boxes are fixed-size markers.** FOMO gives a centroid per grid cell, so the box is a cell around the centroid, not the outline of the cap.
- **Two classes only,** trained on the same dataset as the desktop YOLOv8n model. Fingers and orange backgrounds can still give false positives.
- **Frame rate is not measured end to end.** Inference is about 87 ms, plus the time to send about 40 KB per frame over USB.
- **The viewer needs the board on USB.** It doesn't work over the network.
