"""Extract every Nth frame of a recorded .avi into a dataset folder.

Edit the constants below (class folder + video) before each run:
    python3 tools/extract_frames.py
"""

import sys
from pathlib import Path

import cv2

# record four new videos: one full of empty images for training,
# one with both caps, one for testing the blue caps and one for testing red caps.

ROOT = Path(__file__).resolve().parents[1]

VIDEO_PATH = ROOT / "recordings" / "test-3.avi"
# change to "red" / "blue" depending on the caps in the video
CLASS_NAME = "test"
OUTPUT_DIR = ROOT / "dataset" / CLASS_NAME
# keep 1 frame out of every N
FRAME_STEP = 5


def main():
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        sys.exit(f"could not open video: {VIDEO_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index % FRAME_STEP == 0:
            # video name in the filename avoids overwriting frames from other videos
            out = OUTPUT_DIR / f"{CLASS_NAME}_{VIDEO_PATH.stem}_{index:06d}.jpg"
            cv2.imwrite(str(out), frame)
            saved += 1
        index += 1

    cap.release()
    print(f"read {index} frames, saved {saved} to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
