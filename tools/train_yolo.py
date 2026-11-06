"""Fine-tune YOLOv8n on the blue_cap / red_cap dataset (built for Google Colab).

cell 1:  !pip install -q ultralytics
cell 2:  paste this whole file and run it   (or: !python train_yolo.py)

1. finds the dataset (yolo.zip uploaded to Colab, or dataset/yolo/ locally).
2. loads yolov8n.pt, a model already pretrained on the COCO dataset (80 everyday classes), we only throw classification (last layer) away
3. trains it on our images so it learns the 2 new classes
4. saves soda_caps_best.pt (the final model) + soda_caps_run.zip (plots/logs) and downloads them.

"""

import shutil
import zipfile
from pathlib import Path

import torch
from ultralytics import YOLO

# project root. In a Colab notebook cell __file__ doesn't exist, so fall back to the current folder
ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()

# ---- training settings ----
# maximum number of epochs (early stopping below usually ends training before this)
EPOCHS = 100
# every image is resized to 640x640 before going into the network (YOLO's default size)
IMGSZ = 640
# images processed per weight update (16 fits comfortably in the free Colab T4 GPU memory)
BATCH = 16
# stop early if validation stops improving
# (here: no improvement for 30 epochs in a row -> stop, and keep the best epoch seen so far)
PATIENCE = 30


def find_dataset_yaml():
    """Use yolo.zip (Colab upload) if present, otherwise the local dataset/yolo folder.

    Returns the path of data.yaml, the file that tells YOLO where the train/val/test images are
    and the class names (blue_cap, red_cap). Expected dataset layout:
        images/{train,val,test}/*.jpg    labels/{train,val,test}/*.txt    data.yaml
    """
    # on Colab the uploaded file sits in the working dir or in /content
    for zip_path in (Path("yolo.zip"), Path("/content/yolo.zip")):
        if zip_path.exists():
            target = zip_path.resolve().parent / "yolo_dataset"
            # unzip only once, so re-running the script doesn't extract again
            if not target.exists():
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(target)
            # search recursively because the zip may contain the dataset inside a subfolder
            yamls = sorted(target.rglob("data.yaml"))
            if not yamls:
                raise FileNotFoundError(f"no data.yaml inside {zip_path}")
            return yamls[0]

    # no zip found: running on the PC, use the local dataset folder
    local = ROOT / "dataset" / "yolo" / "data.yaml"
    if local.exists():
        return local
    raise FileNotFoundError("upload yolo.zip next to this script, or create dataset/yolo/data.yaml")


def find_weights():
    """Pick the pretrained starting point (the COCO-trained YOLOv8n)."""
    for path in (Path("yolov8n.pt"), ROOT / "models" / "yolov8n.pt"):
        if path.exists():
            return str(path)
    # ultralytics downloads it automatically
    return "yolov8n.pt"


def main(epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, project=None):
    # absolute path, otherwise ultralytics prefixes it with its own global runs dir
    project = str(Path(project or "runs/soda_caps").resolve())

    # training on CPU would take hours; the GPU makes it a few minutes
    if not torch.cuda.is_available():
        print("WARNING: no GPU found, training will be very slow. "
              "In Colab: Runtime > Change runtime type > T4 GPU, then run again.")

    # ---- STEPS 1-2: find the dataset and load the pretrained model ----
    data = find_dataset_yaml()
    print(f"dataset: {data}")
    # load the pretrained model: this is what makes it transfer learning (fine-tuning)
    model = YOLO(find_weights())

    # ---- STEP 3: training ----
    # at the end of every epoch ultralytics scores the model on the val split and keeps the best
    # epoch as weights/best.pt (and the latest as last.pt)
    model.train(
        data=str(data),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=PATIENCE,
        project=project,
        name="train",
        # overwrite the previous run folder instead of creating train2, train3...
        exist_ok=True,
        # the only difference between the classes is colour, so don't let augmentation shift the hue
        # (augmentation = random changes to the images during training, to help it generalize;
        # the other augmentations like flips, scale and brightness stay on at their defaults)
        hsv_h=0.0,
    )

    save_dir = Path(model.trainer.save_dir)
    # best.pt = weights from the best epoch (not necessarily the last one; in our run, epoch 30 of 58)
    best = save_dir / "weights" / "best.pt"
    print(f"best weights: {best}")

    # ---- STEP 4: evaluation on data the model never trained on ----
    best_model = YOLO(str(best))
    # val = the split used to pick the best epoch; test = completely untouched, so it's the honest score
    for split in ("val", "test"):
        print(f"\n=== {split} split ===")
        try:
            metrics = best_model.val(data=str(data), split=split, project=project, name=f"eval_{split}", exist_ok=True)
        except Exception as e:
            # e.g. the dataset has no test split
            print(f"skipped {split}: {e}")
            continue
        # metrics.box.* are averaged over the 2 classes
        print(f"mAP50: {metrics.box.map50:.3f}  mAP50-95: {metrics.box.map:.3f}  "
              f"precision: {metrics.box.mp:.3f}  recall: {metrics.box.mr:.3f}")

    # ---- STEP 5: export the results ----
    # soda_caps_best.pt = the final model, used by host/vision/yolo_detector.py
    out_weights = Path("soda_caps_best.pt")
    shutil.copy2(best, out_weights)
    # soda_caps_run.zip = the whole run folder (training curves, confusion matrix, sample predictions, logs)
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
