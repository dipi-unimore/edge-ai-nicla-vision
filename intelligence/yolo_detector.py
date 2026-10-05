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

# defaults tensor values for standardization
def tensor_to_numpy(x):
    if isinstance(x, torch.Tensor):
            return x.detach().cpu().numpy()
    return np.array(x)

# draws rectangles over every detected object (no labels or ids yet)
def draw_detections(frame, results, model):
    # used for logging all returned attrs
    print(results)

    # 'results' is a single result instance
    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return frame, []

    xyxy = getattr(boxes, "xyxy", None)
    if xyxy is None:
            return frame, []
    xyxy = tensor_to_numpy(xyxy)

    new_img = frame
    for coords in xyxy:
        xmin, ymin, xmax, ymax = map(int, coords)
        new_img = cv2.rectangle(new_img, (xmin, ymin), (xmax, ymax), (16, 160, 16), 2)

    return new_img

    
def main():
    vidCap = cv2.VideoCapture(0)
    model = YOLO('yolov8n.pt')

    if not vidCap.isOpened():
        raise RuntimeError("couldn't open webcam (index 0)")

    count = 0

    while count < 1:
        ok, frame = vidCap.read()

        if not ok:
                    break
        
        results = model(frame)[0]
        # gets the new_img with drawed rectangles
        new_img = draw_detections(frame, results, model)

        cv2.imshow('webcam', new_img)
        # we have to run this to actually loop the function
        cv2.waitKey(1)
        count += 1

if __name__ == '__main__':
    main()