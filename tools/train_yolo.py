"""Fine-tune YOLOv8n on the blue_cap / red_cap dataset (built for Google Colab, also runs locally).

Colab (Runtime > Change runtime type > T4 GPU), upload yolo.zip (and optionally yolov8n.pt), then:

    cell 1:  !pip install -q ultralytics
    cell 2:  paste this whole file and run it   (or: !python train_yolo.py)

yolo.zip is the dataset folder in the Ultralytics layout (images/{train,val,test}, labels/{train,val,test}, data.yaml).
Locally it uses dataset/yolo/data.yaml.
"""

import shutil
import zipfile
from pathlib import Path

import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()

EPOCHS = 100
IMGSZ = 640
BATCH = 16
# stop early if validation stops improving
PATIENCE = 30


def find_dataset_yaml():
    """Use yolo.zip (Colab upload) if present, otherwise the local dataset/yolo folder."""
    for zip_path in (Path("yolo.zip"), Path("/content/yolo.zip")):
        if zip_path.exists():
            target = zip_path.resolve().parent / "yolo_dataset"
            if not target.exists():
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(target)
            yamls = sorted(target.rglob("data.yaml"))
            if not yamls:
                raise FileNotFoundError(f"no data.yaml inside {zip_path}")
            return yamls[0]

    local = ROOT / "dataset" / "yolo" / "data.yaml"
    if local.exists():
        return local
    raise FileNotFoundError("upload yolo.zip next to this script, or create dataset/yolo/data.yaml")


def find_weights():
    for path in (Path("yolov8n.pt"), ROOT / "models" / "yolov8n.pt"):
        if path.exists():
            return str(path)
    # ultralytics downloads it automatically
    return "yolov8n.pt"


def main(epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, project=None):
    # absolute path, otherwise ultralytics prefixes it with its own global runs dir
    project = str(Path(project or "runs/soda_caps").resolve())

    if not torch.cuda.is_available():
        print("WARNING: no GPU found, training will be very slow. "
              "In Colab: Runtime > Change runtime type > T4 GPU, then run again.")

    data = find_dataset_yaml()
    print(f"dataset: {data}")
    model = YOLO(find_weights())

    model.train(
        data=str(data),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=PATIENCE,
        project=project,
        name="train",
        exist_ok=True,
        # the only difference between the classes is colour, so don't let augmentation shift the hue
        hsv_h=0.0,
    )

    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    print(f"best weights: {best}")

    best_model = YOLO(str(best))
    for split in ("val", "test"):
        print(f"\n=== {split} split ===")
        try:
            metrics = best_model.val(data=str(data), split=split, project=project, name=f"eval_{split}", exist_ok=True)
        except Exception as e:
            print(f"skipped {split}: {e}")
            continue
        print(f"mAP50: {metrics.box.map50:.3f}  mAP50-95: {metrics.box.map:.3f}  "
              f"precision: {metrics.box.mp:.3f}  recall: {metrics.box.mr:.3f}")

    out_weights = Path("soda_caps_best.pt")
    shutil.copy2(best, out_weights)
    out_run = shutil.make_archive("soda_caps_run", "zip", save_dir)
    print(f"\nsaved {out_weights} and {out_run}")

    # auto-download only works when pasted into a notebook cell, not via "!python"; otherwise use the Files panel
    try:
        from google.colab import files
        files.download(str(out_weights))
        files.download(out_run)
    except Exception:
        print("download manually from the Files panel")


if __name__ == "__main__":
    main()
