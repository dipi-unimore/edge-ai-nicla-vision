"""Convert dataset/yolo into an Edge Impulse upload for FOMO (object detection).

Edge Impulse reads YOLO-style boxes from a bounding_boxes.labels JSON file
placed next to the images, in pixel coordinates. FOMO then turns each box
into a centroid by itself, so no extra conversion is needed here.

Output (dataset/fomo/):
    training/   train + val images (Edge Impulse makes its own split inside this)
    testing/    the untouched test images
Each folder has a bounding_boxes.labels file. Images with no caps get an
empty list, so they are learned as background.

Run from the repo root:  .venv/bin/python tools/prepare_fomo_dataset.py
Then upload with the Edge Impulse CLI (see the printed commands).
"""
import json
import shutil
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT / "dataset" / "yolo"
OUT_DIR = ROOT / "dataset" / "fomo"

# class index in the YOLO label files -> label name in Edge Impulse
CLASS_NAMES = {0: "blue_cap", 1: "red_cap"}

# YOLO split -> Edge Impulse category folder
CATEGORY_BY_SPLIT = {
    "train": "training",
    "val": "training",
    "test": "testing",
}


def yolo_to_boxes(label_file: Path, img_w: int, img_h: int) -> list[dict]:
    """Turn one YOLO line 'cls cx cy w h' (normalised) into a pixel box."""
    boxes = []
    for line in label_file.read_text().splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        cls, cx, cy, w, h = int(parts[0]), *map(float, parts[1:])
        bw, bh = w * img_w, h * img_h
        boxes.append({
            "label": CLASS_NAMES[cls],
            "x": round(cx * img_w - bw / 2),
            "y": round(cy * img_h - bh / 2),
            "width": round(bw),
            "height": round(bh),
        })
    return boxes


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    for category in set(CATEGORY_BY_SPLIT.values()):
        (OUT_DIR / category).mkdir(parents=True)

    counts = {c: {"images": 0, "boxes": 0, "background": 0} for c in ("training", "testing")}
    labels_per_category = {c: {"type": "bounding-box-labels", "version": 1, "boundingBoxes": {}}
                           for c in counts}

    for split, category in CATEGORY_BY_SPLIT.items():
        for img_path in sorted((YOLO_DIR / "images" / split).glob("*.jpg")):
            label_path = YOLO_DIR / "labels" / split / (img_path.stem + ".txt")
            if not label_path.exists():
                raise SystemExit(f"missing label for {img_path.name}")

            img = cv2.imread(str(img_path))
            if img is None:
                raise SystemExit(f"cannot read {img_path}")
            h, w = img.shape[:2]

            # unique name across splits, since val and train are merged
            name = f"{split}_{img_path.name}"
            shutil.copy2(img_path, OUT_DIR / category / name)

            boxes = yolo_to_boxes(label_path, w, h)
            labels_per_category[category]["boundingBoxes"][name] = boxes
            counts[category]["images"] += 1
            counts[category]["boxes"] += len(boxes)
            if not boxes:
                counts[category]["background"] += 1

    for category, labels in labels_per_category.items():
        (OUT_DIR / category / "bounding_boxes.labels").write_text(json.dumps(labels, indent=2))

    for category, c in counts.items():
        print(f"{category}: {c['images']} images, {c['boxes']} boxes, {c['background']} background")

    print("\nUpload with the Edge Impulse CLI (needs an API key for your project):")
    print(f"  edge-impulse-uploader --category training --directory {OUT_DIR / 'training'}")
    print(f"  edge-impulse-uploader --category testing --directory {OUT_DIR / 'testing'}")


if __name__ == "__main__":
    main()
