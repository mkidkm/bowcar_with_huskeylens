// Host simulation only. These definitions do not validate AVR hardware or RAM.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <deque>

#define F(x) x
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define INPUT_PULLUP 2
const int A0=14, A1=15, A2=16, A3=17, A4=18, A5=19, A6=20, A7=21;
extern unsigned long fakeClock;
extern int fakePwm[32], fakeDigital[32];
inline unsigned long millis() { return fakeClock++; }
inline void delay(unsigned long ms) { fakeClock += ms; }
inline void pinMode(int, int) {}
inline void analogWrite(int pin, int value) { fakePwm[pin] = value; }
inline void digitalWrite(int pin, int value) { fakeDigital[pin] = value; }
inline int analogRead(int) { return 0; }
inline int digitalRead(int) { return 1; }
inline unsigned long pulseIn(int, int, unsigned long=1000000UL) { return 0; }
inline void delayMicroseconds(unsigned int) {}
template<class T> inline T min(T a, T b) { return std::min(a,b); }
template<class T> inline T max(T a, T b) { return std::max(a,b); }

class String : public std::string {
public:
  String(const char* value): std::string(value) {}
  void toCharArray(char* target, unsigned int length) const {
    if (length) { std::strncpy(target, c_str(), length-1); target[length-1]=0; }
  }
};
class Stream {
public:
  void begin(int) {}
  size_t write(uint8_t*, int length) { return length; }
  int available() { return 0; }
  int read() { return -1; }
  template<class T> void print(T) {}
  template<class T> void println(T) {}
};
extern Stream Serial;
