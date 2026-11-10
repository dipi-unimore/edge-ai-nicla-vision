"""Add negative frames (no caps) to the YOLO dataset.

Negatives need no boxes: each image gets an empty .txt label file.
Each recording goes to a single split so near-identical frames from one
video never end up in both train and val.

Run from the repo root:  python tools/add_negatives.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEG_DIR = ROOT / "dataset" / "negatives"
YOLO_DIR = ROOT / "dataset" / "yolo"

# recording stem -> split
SPLIT_BY_RECORDING = {
    "negatives_negative-1": "train",
    "negatives_negative-2": "val",
}


def main() -> None:
    added = {"train": 0, "val": 0}
    for img in sorted(NEG_DIR.glob("*.jpg")):
        recording = img.stem.rsplit("_", 1)[0]
        split = SPLIT_BY_RECORDING.get(recording)
        if split is None:
            raise SystemExit(f"No split configured for {img.name}")

        img_dst = YOLO_DIR / "images" / split / img.name
        lbl_dst = YOLO_DIR / "labels" / split / (img.stem + ".txt")
        if img_dst.exists() or lbl_dst.exists():
            raise SystemExit(f"Refusing to overwrite existing file: {img_dst.name}")

        shutil.copy2(img, img_dst)
        lbl_dst.touch()
        added[split] += 1

    for split, n in added.items():
        total = len(list((YOLO_DIR / "images" / split).glob("*.jpg")))
        labels = len(list((YOLO_DIR / "labels" / split).glob("*.txt")))
        print(f"{split}: added {n} negatives -> {total} images, {labels} labels")


if __name__ == "__main__":
    main()
