# Intelligence

[← Back to main README](../README.md)

The development of intelligence in the project is split into 2 main different phases. A development phase on a desktop machine using YOLOv8n/openCV for video and librosa/tensorflow for audio, and an integration phase into the board using TinyML.

## Video

Video intelligence on the machine has been developed using openCV, an open-source library for real-time computer vision and image processing. The model used was YOLOv8n, specifically chosen for its small size and interesting didactic value.

The demo *yolo_detector.py* can be seen inside the `host/vision/` folder and it describes the implementation of object detection and classification with bounding boxes, labels and confidence scores over the YOLOv8n model.

<!--! 📸 GIF: webcam demo with bounding boxes, labels and confidence scores appearing live (this is your strongest visual) -->

## Audio

Audio intelligence on the machine is currently undergoing development.

As of now, audio recording and melspectrogram plotting has been implemented and can be seen described on the script *mel_spectrogram.py*, inside the `host/audio/` folder. The libs used were sounddevice for audio recording and librosa for melspectrogram plotting.

<!-- ! 📸 IMAGEs: example melspectrograms of 2-3 different spoken keywords side by side -->

### Keyword spotting (KWS)

A keyword-spotting model for 10 different words is under development.

<!-- 📸 IMAGE: training curves (accuracy/loss) and confusion matrix once the model is done -->
<!-- 📸 GIF: real-time keyword detection demo -->