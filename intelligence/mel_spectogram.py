"""Audio recorder using sounddevice and melspectogram generator using librosa.
Intermediary step between audio fundamentals and audio model classification for KWS.

Usage:
python intelligence/kws.py out.wav -s 16000 -c 1 -d 5
python intelligence/kws.py --list-devices
"""

import numpy as np
import sounddevice as sd
import librosa
import cv2

def record_audio(duration, sr):
    print(f"Recording {duration}s audio...")
    rec = sd.rec(int(duration * sr), samplerate=sr, channels=1, device=4)
    sd.wait()
    return rec.flatten(), sr

def make_mel_spectrogram_image(audio_rec, sr):
    if audio_rec is None:
        return None
    # n_mels is the number of frequency bands (image rows). kws uses about 40 usually
    mel = librosa.feature.melspectrogram(y=audio_rec, sr=sr, n_mels=128)
    # scales to dBs, as humans listen (logarithmic scale)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    # normalize to 0-255 for display
    img = (255 * (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-6)).astype(np.uint8)
    return cv2.applyColorMap(cv2.resize(img, (640, 256)), cv2.COLORMAP_INFERNO)

def record_handler():
    # debug audio recording:
    # print(audio_rec.max(), image.min(), image.max())
    audio_rec, sr = record_audio(1, 16000)
    image = make_mel_spectrogram_image(audio_rec, sr)
    return image

def main():
    spectrogram_image = record_handler()
    cv2.imshow('mel-spectrogram', spectrogram_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()