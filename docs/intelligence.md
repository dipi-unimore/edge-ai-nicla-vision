# Intelligence

[← Back to main README](../README.md)

The development of intelligence in the project is split into 2 main different phases. A development phase on a desktop machine using YOLOv8n/openCV for video and librosa/tensorflow for audio, and an integration phase into the board using TinyML.

## Video

Video intelligence on the machine has been developed using openCV, an open-source library for real-time computer vision and image processing. The model used was YOLOv8n, specifically chosen for its small size and interesting didactic value.

The demo *yolo_detector.py* can be seen inside the `host/vision/` folder and it describes the implementation of object detection and classification with bounding boxes, labels and confidence scores over the YOLOv8n model.

### Custom classes: blue and red soda caps

The stock YOLOv8n only knows the 80 COCO classes, and its classification head can't simply be extended with new ones. To detect a **blue cap** and a **red cap**, the pretrained model was fine-tuned (transfer learning) on a small dataset built for this project. The COCO classes are dropped in the process: the fine-tuned model detects only the two caps.

<!-- 📸 GIF: live detection of the blue and red caps from the webcam.
Save it as assets/yolo_caps_demo.gif and replace this comment with:

<p align="center">
    <img src="../assets/yolo_caps_demo.gif" width="600"/>
    <br/><em>Live detection of the blue and red caps</em>
</p>
-->

The process, from images to model:

1. **Collecting frames:** short videos with blue caps, red caps and both together were recorded, and every 5th frame was extracted as a still image.
2. **Labeling in [CVAT](https://www.cvat.ai/):** the frames were uploaded as tasks, bounding boxes were drawn around each cap with the labels `blue_cap` and `red_cap`, and each task was assigned a subset (Train, Validation or Test). Frames with no cap were kept as negative examples. The project was exported in the **YOLO 1.1** format, which gives one `.txt` file per image with the class and the normalized box.
3. **Building the dataset:** CVAT's free tier doesn't allow exporting the images together with the labels, so the export contains only the label files. Each label was matched back to its original frame by file name, and the result was arranged in the Ultralytics folder layout (`images/` and `labels/` split into `train`, `val` and `test`, plus a `data.yaml` with the two class names).
4. **Training on Google Colab:** the dataset was zipped, uploaded to Colab and [tools/train_yolo.py](../tools/train_yolo.py) was run on the free T4 GPU. It fine-tunes `yolov8n.pt` (640 px, up to 100 epochs, early stopping), evaluates the best weights on the validation and test splits and saves the result. Training stopped at epoch 58 (about 4.5 minutes) and kept the weights from epoch 28.
5. **Using the model:** the resulting `models/soda_caps_best.pt` is loaded by `yolo_detector.py` in place of the stock weights.

<!-- 📸 IMAGE: screenshot of the CVAT labeling interface with a blue and a red cap boxed.
Save it as assets/cvat_labeling.png and replace this comment with:

<p align="center">
    <img src="../assets/cvat_labeling.png" width="700"/>
    <br/><em>Labeling the caps in CVAT</em>
</p>
-->

<!-- 📸 IMAGE (optional): screenshot of the Colab training run (epoch progress and final metrics table).
Save it as assets/colab_training.png and replace this comment with:

<p align="center">
    <img src="../assets/colab_training.png" width="700"/>
    <br/><em>Fine-tuning on a free Colab GPU</em>
</p>
-->

Two choices worth noting:

- **The split is by recording, not by frame.** Consecutive frames are nearly identical, so a random split would leak training frames into validation and inflate the scores. Training uses the single-color videos (one color per video), validation the video with both caps, and test separate videos not used in training.
- **Hue augmentation is turned off** (`hsv_h=0`). The two classes differ mostly by color, and a hue shift could turn a blue cap into a red one.

| Split | Images | Cap boxes | Images without caps |
|-------|--------|-----------|---------------------|
| Train | 293 | 269 | 28 |
| Validation | 57 | 47 | 27 |
| Test | 72 | 54 | 30 |

| Split | mAP50 | mAP50-95 | Precision | Recall |
|-------|-------|----------|-----------|--------|
| Validation | 0.970 | 0.723 | 0.909 | 0.881 |
| Test | 0.931 | 0.688 | 0.833 | 0.908 |

<p align="center">
    <img src="../assets/yolo_val_predictions.jpg" width="700"/>
    <br/><em>Predictions on validation frames: caps found against sunlit, cluttered backgrounds</em>
</p>

#### Known limitation: false positives

Real caps are found reliably, but the model also fires on things that are not caps. In live tests the most common false `red_cap` detections are fingers and orange-ish backgrounds. Counting detections against the labels (IoU 0.5), the test split has 54 real caps and at the default confidence threshold of 0.25 all of them are found, along with 31 false detections (15 `red_cap`, 16 `blue_cap`). Raising the threshold to 0.5 reduces the false detections to 22 at the cost of 1 missed cap. The validation split behaves the same way, with `red_cap` the worse offender at 0.25 (26 false detections against 14 for `blue_cap`).

<p align="center">
    <img src="../assets/yolo_confusion_matrix.png" width="450"/>
    <br/><em>Normalized confusion matrix on validation: every real cap is detected (diagonal), but the detections on background are split 37% blue / 63% red</em>
</p>

The likely cause is how few negative examples the dataset has: only 28 of 293 training images contain no cap. 

Adding more negatives, especially hands and orange objects, is the next improvement, and it will benefit the FOMO model for the board, which is trained on the same dataset.

## Audio

Audio intelligence on the machine is currently undergoing development.

As of now, audio recording and melspectrogram plotting has been implemented and can be seen described on the script *mel_spectrogram.py*, inside the `host/audio/` folder. The libs used were sounddevice for audio recording and librosa for melspectrogram plotting.

<!-- ! 📸 IMAGEs: example melspectrograms of 2-3 different spoken keywords side by side -->

### Keyword spotting (KWS)

A keyword-spotting model for 10 different words is under development.

<!-- 📸 IMAGE: training curves (accuracy/loss) and confusion matrix once the model is done -->
<!-- 📸 GIF: real-time keyword detection demo -->