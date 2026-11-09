/* Live FOMO detections streamed over USB serial to host/vision/fomo_viewer.py.
 * Requires the nicla-vision-caps-detection_inferencing Arduino library.
 *
 * Packet per frame: MAGIC(4) | count(1) | ms(2, LE) | count x [class, conf, x, y, w, h] | 160x120 RGB565 frame
 */
#include <nicla-vision-caps-detection_inferencing.h>

#include "edge-impulse-sdk/dsp/image/image.hpp"

#include "camera.h"
#include "gc2145.h"
#include <ea_malloc.h>
#include <string.h>

#define FRAME_W 320
#define FRAME_H 240
#define DISPLAY_W 160
#define DISPLAY_H 120
#define MAX_DETECTIONS 16

// The model sees the centered 240x240 crop (x offset 40) scaled to 96x96.
// Model coords -> display coords (160x120): x = (40 + x*2.5) / 2, y = (y*2.5) / 2.
#define CROP_OFFSET_X 20
#define MODEL_TO_DISPLAY 1.25f

static const uint8_t PACKET_MAGIC[4] = {0xDE, 0xAD, 0xBE, 0xEF};

GC2145 galaxyCore;
Camera cam(galaxyCore);
FrameBuffer fb;

static uint8_t *frame_rgb565;
static uint8_t *frame_rgb888;
static uint8_t display_row[DISPLAY_W * 2];

static uint8_t *align32(void *p) {
    return (uint8_t *)(((uintptr_t)p + 31) & ~(uintptr_t)31);
}

static void rgb565_to_rgb888(const uint8_t *src, uint8_t *dst, uint32_t pixels) {
    for (uint32_t i = 0; i < pixels; i++) {
        uint8_t hb = *src++;
        uint8_t lb = *src++;
        *dst++ = hb & 0xF8;
        *dst++ = (hb & 0x07) << 5 | (lb & 0xE0) >> 3;
        *dst++ = (lb & 0x1F) << 3;
    }
}

static int get_model_input(size_t offset, size_t length, float *out_ptr) {
    for (size_t i = 0; i < length; i++) {
        const uint8_t *p = &frame_rgb888[(offset + i) * 3];
        out_ptr[i] = (p[0] << 16) + (p[1] << 8) + p[2];
    }
    return 0;
}

void setup() {
    Serial.begin(115200);
    while (!Serial);

    malloc_addblock((void *)0x30000000, 288 * 1024);

    if (!cam.begin(CAMERA_R320x240, CAMERA_RGB565, -1)) {
        while (1);
    }

    frame_rgb565 = align32(ei_malloc(FRAME_W * FRAME_H * 2 + 32));
    frame_rgb888 = align32(ea_malloc(FRAME_W * FRAME_H * 3 + 32));
    if (frame_rgb565 == NULL || frame_rgb888 == NULL) {
        while (1);
    }
    fb.setBuffer(frame_rgb565);
}

void loop() {
    if (cam.grabFrame(fb, 100) != 0) {
        return;
    }

    rgb565_to_rgb888(frame_rgb565, frame_rgb888, FRAME_W * FRAME_H);
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
    uint16_t inference_ms = millis() - start;

    uint8_t dets[MAX_DETECTIONS * 6];
    uint8_t count = 0;
    for (uint32_t i = 0; i < result.bounding_boxes_count && count < MAX_DETECTIONS; i++) {
        ei_impulse_result_bounding_box_t bb = result.bounding_boxes[i];
        if (bb.value <= 0) {
            continue;
        }
        uint8_t *d = &dets[count * 6];
        d[0] = strcmp(bb.label, "red_cap") == 0 ? 1 : 0;
        d[1] = (uint8_t)(bb.value * 255);
        d[2] = (uint8_t)(CROP_OFFSET_X + bb.x * MODEL_TO_DISPLAY);
        d[3] = (uint8_t)(bb.y * MODEL_TO_DISPLAY);
        d[4] = (uint8_t)(bb.width * MODEL_TO_DISPLAY);
        d[5] = (uint8_t)(bb.height * MODEL_TO_DISPLAY);
        count++;
    }

    Serial.write(PACKET_MAGIC, sizeof(PACKET_MAGIC));
    Serial.write(&count, 1);
    uint8_t ms_bytes[2] = {(uint8_t)(inference_ms & 0xFF), (uint8_t)(inference_ms >> 8)};
    Serial.write(ms_bytes, 2);
    Serial.write(dets, count * 6);

    // Decimate the raw 320x240 frame to 160x120 (every other pixel and row).
    for (uint32_t y = 0; y < DISPLAY_H; y++) {
        const uint8_t *src = &frame_rgb565[(2 * y * FRAME_W) * 2];
        for (uint32_t x = 0; x < DISPLAY_W; x++) {
            display_row[2 * x] = src[4 * x];
            display_row[2 * x + 1] = src[4 * x + 1];
        }
        Serial.write(display_row, sizeof(display_row));
    }
}
