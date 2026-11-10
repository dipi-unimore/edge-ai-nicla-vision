"""Live window for the FOMO firmware in board/fomo_live.

Reads the packets sent over USB serial by the Nicla Vision and draws
bounding boxes and centroids for blue_cap / red_cap on a live frame.

Usage: python fomo_viewer.py --port /dev/ttyACM0
"""

import argparse
import struct
import sys

import cv2
import numpy as np
import serial

MAGIC = bytes([0xDE, 0xAD, 0xBE, 0xEF])
FRAME_W, FRAME_H = 160, 120
FRAME_BYTES = FRAME_W * FRAME_H * 2
LABELS = ["blue_cap", "red_cap"]
COLORS = [(255, 128, 0), (0, 0, 255)]  # BGR
SCALE = 4


def read_exact(ser, n):
    buf = b""
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if not chunk:
            raise TimeoutError("no data from board")
        buf += chunk
    return buf


def sync(ser):
    window = b""
    while True:
        window = (window + ser.read(1))[-4:]
        if window == MAGIC:
            return


def rgb565_to_bgr(raw):
    px = np.frombuffer(raw, dtype=np.uint8).reshape(FRAME_H, FRAME_W, 2)
    hb = px[..., 0].astype(np.uint16)
    lb = px[..., 1].astype(np.uint16)
    r = (hb & 0xF8)
    g = ((hb & 0x07) << 5) | ((lb & 0xE0) >> 3)
    b = (lb & 0x1F) << 3
    return np.dstack([b, g, r]).astype(np.uint8)


def draw(frame, detections, ms):
    img = cv2.resize(frame, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_NEAREST)
    for cls, conf, x, y, w, h in detections:
        color = COLORS[cls]
        x0, y0 = int(x * SCALE), int(y * SCALE)
        x1, y1 = int((x + w) * SCALE), int((y + h) * SCALE)
        cx, cy = int((x + w / 2) * SCALE), int((y + h / 2) * SCALE)
        cv2.rectangle(img, (x0, y0), (x1, y1), color, 2)
        cv2.circle(img, (cx, cy), 5, color, -1)
        cv2.putText(img, f"{LABELS[cls]} {conf / 255:.2f}", (x0, max(y0 - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    cv2.putText(img, f"{ms} ms  {len(detections)} det", (8, img.shape[0] - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return img


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=2)
    print(f"Reading from {args.port}. Press q in the window to quit.")
    try:
        while True:
            sync(ser)
            count, ms = struct.unpack("<BH", read_exact(ser, 3))
            dets = [struct.unpack("6B", read_exact(ser, 6)) for _ in range(count)]
            frame = rgb565_to_bgr(read_exact(ser, FRAME_BYTES))
            cv2.imshow("Nicla Vision FOMO", draw(frame, dets, ms))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except (TimeoutError, serial.SerialException) as e:
        print(f"Stopped: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
