"""YOLO Object Detection with Webcam
Captures video from webcam and runs YOLOv8n object detection.

Features:
- Initializes camera using cv2.VideoCapture(0)
- Captures each frame in a loop
- Runs YOLOv8n inference on each frame
- Draws bounding box + label + cfs around detected objects
- Appends detections on structured payload
- Publishes payload via broker.

USAGE:
source .venv/bin/activate
python3 intelligence/yolo_detector.py
"""

# todo: better structure (no logic change). must revisit!

import cv2
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import json
from pathlib import Path

# change based on desire model to run
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "soda_caps_best.pt"
# detections below this confidence are dropped (higher = fewer false positives, but more missed objects)
CONF_THRESHOLD = 0.5

def setup_mqtt():
    mqttc = mqtt.Client(client_id="openmv")
    try:
        mqttc.connect("localhost", 1883, keepalive=60)
        mqttc.loop_start()
        print("connected to MQTT broker")
        return mqttc
    except Exception as e:
        print(f"could not connect to MQTT broker: {e}")

# draws rectangles with labels and confidence scores
def draw_detections(frame, results, model):
    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return frame, []
    
    # coordinates of the boxes returned by 'results'
    xyxy = getattr(boxes, "xyxy", None)
    if xyxy is None:
            return frame, []
    
    cls = getattr(boxes, "cls", None)
    conf = getattr(boxes, "conf", None)

    detections = []
    new_img = frame

    for i, coords in enumerate(xyxy):
        xmin, ymin, xmax, ymax = map(int, coords)
        # class id from the detected object
        class_id = int(cls[i])
        # extract tensor value from obj with 4 places precision
        cfs = f"{conf[i].item():.4f}"
        label = model.names.get(class_id, str(class_id)) if hasattr(model, 'names') else str(class_id)

        # calculations for text placement
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_size = label_size[0] + 86

        # places text and draws rectangle over detected object's box
        cv2.rectangle(new_img, (xmin, ymin-15), (xmin+text_size, ymin), (16, 160, 16), -1)
        cv2.rectangle(new_img, (xmin, ymin), (xmax, ymax), (16, 160, 16), 2)
        cv2.putText(new_img, label, (xmin, ymin-4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(new_img, f" - {cfs}", (xmin + label_size[0], ymin-4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # payload to be transmitted via broker
        detections.append({
            "label": label,
            "confidence": cfs,
            "class_id": class_id,
            "coords": [xmin, ymin, xmax, ymax]
        })

    return new_img, detections

    
def main():
    vidCap = cv2.VideoCapture(0)
    model = YOLO(MODEL_PATH)
    mqttc = setup_mqtt()

    if not vidCap.isOpened():
        raise RuntimeError("couldn't open webcam (index 0)")

    while True:
        ok, frame = vidCap.read()
        if not ok:
            break    

        results = model(frame, conf=CONF_THRESHOLD)[0]
        new_img, detections = draw_detections(frame, results, model)
        cv2.imshow('webcam', new_img)

        if mqttc is not None and detections:
            mqttc.publish("openmv/yolov8n", json.dumps(detections))

        # we have to run this to actually loop the function
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

if __name__ == '__main__':
    main()