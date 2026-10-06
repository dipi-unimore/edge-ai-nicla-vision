"""YOLO Object Detection with Webcam
Captures video from webcam and runs YOLOv8n object detection.

Features:
- Initializes camera using cv2.VideoCapture(0)
- Captures each frame in a loop
- Runs YOLOv8n inference on each frame
- Draws bounding boxes around detected objects
- Displays results in real-time window

USAGE:
source .venv/bin/activate
python3 intelligence/yolo_detector.py
"""

# * futurally, implement stuff to make code "better" such as:
# try:
#     from ultralytics import YOLO
# except Exception as e:
#     raise SystemExit("ultralytics missing, run: pip install ultralytics")

import cv2
from ultralytics import YOLO
import torch
import numpy as np
import paho.mqtt.client as mqtt
import json

mqttc = mqtt.Client(client_id="openmv")

# connect to MQTT broker with error handling
try:
    mqttc.connect("localhost", 1883, keepalive=60)
    mqttc.loop_start()
    print("connected to MQTT broker")
except Exception as e:
    print(f"could not connect to MQTT broker: {e}")

# defaults tensor values for standardization
def tensor_to_numpy(x):
    if isinstance(x, torch.Tensor):
            return x.detach().cpu().numpy()
    return np.array(x)

# draws rectangles with labels (missing confidence scores)
def draw_detections(frame, results, model):
    # 'results' is a single result instance
    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return frame, []

    xyxy = getattr(boxes, "xyxy", None)
    if xyxy is None:
            return frame, []
    xyxy = tensor_to_numpy(xyxy)
    cls = getattr(boxes, "cls", None)

    detections = []
    new_img = frame
    for i, coords in enumerate(xyxy):
        xmin, ymin, xmax, ymax = map(int, coords)
        # class id from the detected object
        class_id = int(cls[i])
        label = model.names.get(class_id, str(class_id)) if hasattr(model, 'names') else str(class_id)
        # places text and draws rectangle over detected object's box
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.rectangle(new_img, (xmin, ymin-15), (xmin+t_size[0], ymin), (16, 160, 16), -1)
        cv2.rectangle(new_img, (xmin, ymin), (xmax, ymax), (16, 160, 16), 2)
        cv2.putText(new_img, label, (xmin, ymin-4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # payload to be transmitted via broker
        detections.append({
            "label": label,
            "class_id": class_id,
            "coords": [xmin, ymin, xmax, ymax] 
        })

    return new_img, detections

    
def main():
    vidCap = cv2.VideoCapture(0)
    model = YOLO('yolov8n.pt')
    if not vidCap.isOpened():
        raise RuntimeError("couldn't open webcam (index 0)")
    
    while True:
        ok, frame = vidCap.read()
        if not ok:
            break      
        results = model(frame)[0]
        new_img, detections = draw_detections(frame, results, model)
        cv2.imshow('webcam', new_img)
        mqttc.publish("openmv/yolov8n", json.dumps(detections))
        # we have to run this to actually loop the function
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

if __name__ == '__main__':
    main()