// Host-only pixel buffer. This does not simulate physical LEDs or signal timing.
#pragma once
#include "Arduino.h"

#define NEO_GRB 0
#define NEO_KHZ800 0

class Adafruit_NeoPixel {
  std::vector<uint32_t> pixels;
  uint8_t brightness=255;
public:
  Adafruit_NeoPixel(uint16_t count, uint8_t, uint16_t): pixels(count, 0) {}
  void begin() {}
  void show() {}
  void clear() { std::fill(pixels.begin(), pixels.end(), 0); }
  void setBrightness(uint8_t value) { brightness=value; }
  void setPixelColor(uint16_t index, uint32_t color) {
    if (index<pixels.size()) pixels[index]=color;
  }
  static uint32_t Color(uint8_t red, uint8_t green, uint8_t blue) {
    return (static_cast<uint32_t>(red)<<16) |
           (static_cast<uint32_t>(green)<<8) | blue;
  }
};
