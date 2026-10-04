"""cv camera capture simplest loop:
- initializes camera using cv2.VideoCapture(0)
- runsa while true that gets cv2.VideoCapture(0).read() (this captures each and every frame)
- shows the image using cv2.imshow('<desired-name-of-window>', frame)

USAGE:
source .venv/bin/activate
python3 intelligence/yolo.py
"""

import cv2

vidCap = cv2.VideoCapture(0)

if not vidCap.isOpened():
    raise RuntimeError("couldn't open webcam (index 0)")

while True:
    ok, frame = vidCap.read()
    if not ok:
        break
    cv2.imshow('webcam', frame)
    cv2.waitKey(1)