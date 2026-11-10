/*
  Streams live FOMO detections over USB serial to host/vision/fomo_viewer.py.
 
  to run:
    python3 -m venv .venv
    source .venv/bin/activate
    pip install opencv-python numpy pyserial
    python3 host/vision/fomo_viewer.py --port /dev/ttyACM0 --baud 115200
 */
#include <nicla-vision-caps-detection_inferencing.h>
#include "edge-impulse-sdk/dsp/image/image.hpp"
#include "camera.h"
#include "gc2145.h"
#include <ea_malloc.h>
#include <string.h>

constexpr int FRAME_W = 320;
constexpr int FRAME_H = 240;
constexpr int PREVIEW_W = 160;
constexpr int PREVIEW_H = 120;
constexpr int MAX_DETECTIONS = 16;

// the model sees the centered 240x240 crop, so boxes are shifted by 20 px and scaled by 1.25
// to land on the 160x120 preview.
constexpr int CROP_OFFSET_X = 20;
constexpr float MODEL_TO_PREVIEW = 1.25f;

constexpr uint8_t MAGIC[4] = {0xDE, 0xAD, 0xBE, 0xEF};
constexpr int HEADER_SIZE = 7;   // magic + count + ms
constexpr int DETECTION_SIZE = 6;

GC2145 galaxyCore;
Camera cam(galaxyCore);
FrameBuffer fb;

// camera frame, rgb565. the camera driver needs it 32 byte aligned.
static uint16_t frame[FRAME_H][FRAME_W] __attribute__((aligned(32)));
// rgb888 copy of the frame used by the model. too big for the normal heap, see setup().
static uint8_t *frame_rgb888;

// converts 2-byte rgb565 pixels into 3-byte rgb888 pixels.
static void rgb565_to_rgb888(const uint8_t *src, uint8_t *dst, int pixels) {
    for (int i = 0; i < pixels; i++, src += 2, dst += 3) {
        dst[0] = src[0] & 0xF8;
        dst[1] = ((src[0] & 0x07) << 5) | ((src[1] & 0xE0) >> 3);
        dst[2] = (src[1] & 0x1F) << 3;
    }
}

// the classifier reads its input through this: one packed 0xRRGGBB number per pixel.
static int get_model_input(size_t offset, size_t length, float *out) {
    for (size_t i = 0; i < length; i++) {
        const uint8_t *p = &frame_rgb888[(offset + i) * 3];
        out[i] = (p[0] << 16) | (p[1] << 8) | p[2];
    }
    return 0;
}

void setup() {
    Serial.begin(115200);
    while (!Serial);

    // the rgb888 frame is too big for the normal heap, so it lives in a separate SRAM block.
    malloc_addblock((void *)0x30000000, 288 * 1024);
    frame_rgb888 = (uint8_t *)ea_malloc(FRAME_W * FRAME_H * 3);

    if (frame_rgb888 == NULL || !cam.begin(CAMERA_R320x240, CAMERA_RGB565, -1)) {
        while (1);
    }
    // the board is mounted upside down, so flipping both axes rotates the image 180 degrees.
    cam.setVerticalFlip(true);
    cam.setHorizontalMirror(true);

    fb.setBuffer((uint8_t *)frame);
}

void loop() {
    if (cam.grabFrame(fb, 100) != 0) {
        return;
    }

    // rgb888 is what the model expects. the crop and resize happen in place.
    rgb565_to_rgb888((const uint8_t *)frame, frame_rgb888, FRAME_W * FRAME_H);
    ei::image::processing::crop_and_interpolate_rgb888(
        frame_rgb888, FRAME_W, FRAME_H,
        frame_rgb888, EI_CLASSIFIER_INPUT_WIDTH, EI_CLASSIFIER_INPUT_HEIGHT);

    ei::signal_t signal;
    signal.total_length = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
    signal.get_data = &get_model_input;

    ei_impulse_result_t result = {0};
    unsigned long start = millis();
    if (run_classifier(&signal, &result, false) != EI_IMPULSE_OK) {
        return;
    }
    uint16_t ms = millis() - start;

    // packet = header followed by one 6-byte record per detection.
    uint8_t packet[HEADER_SIZE + MAX_DETECTIONS * DETECTION_SIZE];
    memcpy(packet, MAGIC, 4);
    packet[5] = ms & 0xFF;  // little endian, as the viewer expects
    packet[6] = ms >> 8;

    int count = 0;
    for (uint32_t i = 0; i < result.bounding_boxes_count && count < MAX_DETECTIONS; i++) {
        const ei_impulse_result_bounding_box_t &bb = result.bounding_boxes[i];
        if (bb.value <= 0) {  // fomo marks empty cells with 0
            continue;
        }
        uint8_t *d = &packet[HEADER_SIZE + count * DETECTION_SIZE];
        d[0] = strcmp(bb.label, "red_cap") == 0;  // 0 = blue_cap, 1 = red_cap
        d[1] = bb.value * 255;
        d[2] = CROP_OFFSET_X + bb.x * MODEL_TO_PREVIEW;
        d[3] = bb.y * MODEL_TO_PREVIEW;
        d[4] = bb.width * MODEL_TO_PREVIEW;
        d[5] = bb.height * MODEL_TO_PREVIEW;
        count++;
    }
    packet[4] = count;
    Serial.write(packet, HEADER_SIZE + count * DETECTION_SIZE);

    // half-size preview: every other pixel of every other row, sent one row at a time.
    uint16_t row[PREVIEW_W];
    for (int y = 0; y < PREVIEW_H; y++) {
        for (int x = 0; x < PREVIEW_W; x++) {
            row[x] = frame[2 * y][2 * x];
        }
        Serial.write((const uint8_t *)row, sizeof(row));
    }
}
