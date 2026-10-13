// Host observations only: no physical motor, LED, power, or sensor validation.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>

#define F(value) value
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define INPUT_PULLUP 2
const int A0=14, A1=15, A2=16, A3=17, A4=18, A5=19, A6=20, A7=21;

struct OutputEvent { unsigned long time; int pin, value; bool pwm; };
struct LogEvent { unsigned long time; std::string text; };
struct EchoEvent { unsigned long timeout; int left, right; };
extern unsigned long fakeClock, fakeEchoUs;
extern int fakePwm[32], fakeDigital[32], fakeInputs[32], fakeAnalog[32];
extern std::vector<OutputEvent> outputEvents;
extern std::vector<LogEvent> logEvents;
extern std::vector<EchoEvent> echoEvents;

inline unsigned long millis() { return fakeClock; }
inline void delay(unsigned long ms) { fakeClock+=ms; }
inline void delayMicroseconds(unsigned int) {} // Sub-ms trigger timing is not simulated.
inline void pinMode(int, int) {}
inline void analogWrite(int pin, int value) {
  fakePwm[pin]=value;
  outputEvents.push_back({fakeClock,pin,value,true});
}
inline void digitalWrite(int pin, int value) {
  fakeDigital[pin]=value;
  outputEvents.push_back({fakeClock,pin,value,false});
}
inline int digitalRead(int pin) { return fakeInputs[pin]; }
inline int analogRead(int pin) { return fakeAnalog[pin]; }
inline unsigned long pulseIn(int, int, unsigned long timeout=1000000UL) {
  echoEvents.push_back({timeout,fakePwm[5],fakePwm[6]});
  fakeClock+=(fakeEchoUs ? std::min(fakeEchoUs,timeout) : timeout)/1000UL;
  return fakeEchoUs<=timeout ? fakeEchoUs : 0;
}
template<class T> inline T min(T a,T b) { return std::min(a,b); }
template<class T> inline T max(T a,T b) { return std::max(a,b); }

class Stream {
  std::string pending;
public:
  void begin(int) {}
  int available() { return 0; }
  int read() { return -1; }
  template<class T> void print(const T& value) {
    std::ostringstream text;
    text<<value;
    pending+=text.str();
  }
  template<class T> void println(const T& value) {
    print(value);
    logEvents.push_back({fakeClock,pending});
    pending.clear();
  }
};
extern Stream Serial;
