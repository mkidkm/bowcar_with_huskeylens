// Simulated HUSKYLENS device speaking the manufacturer's framed I2C protocol.
#pragma once
#include "Arduino.h"
#define WIRE_HAS_TIMEOUT 1

struct FakeResult {
  int command, first, second, third, fourth, id;
};

class TwoWire {
  std::vector<uint8_t> tx;
  std::deque<uint8_t> pending, rx;
  void frame(int command, const std::vector<int>& fields) {
    std::vector<uint8_t> packet={0x55,0xaa,0x11,static_cast<uint8_t>(fields.size()*2),
                                 static_cast<uint8_t>(command)};
    for (int value: fields) {
      uint16_t v=static_cast<uint16_t>(value);
      packet.push_back(v&255); packet.push_back((v>>8)&255);
    }
    uint8_t sum=0;
    for (uint8_t b: packet) sum+=b;
    packet.push_back(sum);
    for (uint8_t b: packet) pending.push_back(b);
  }
public:
  bool cameraAlive=true, algorithmAck=true;
  int lastAlgorithm=-1, lastRequest=-1, lastAddress=-1;
  int algorithmCount=0, knockCount=0, requestCount=0;
  unsigned long timeout=0;
  std::vector<FakeResult> results;
  void begin() {}
  void setWireTimeout(unsigned long us, bool) { timeout=us; }
  void beginTransmission(int address) { lastAddress=address; tx.clear(); }
  size_t write(uint8_t* data, int length) {
    tx.assign(data,data+length); return length;
  }
  int endTransmission() {
    if (tx.size()<6) return 4;
    int command=tx[4];
    if (command==0x2c) ++knockCount;
    else if (command==0x2d) ++algorithmCount;
    else ++requestCount;
    if (!cameraAlive) return 4;
    if (command==0x2c) { frame(0x2e,{}); return 0; } // knock -> OK
    if (command==0x2d) {
      lastAlgorithm=tx[5] | (static_cast<int>(tx[6])<<8);
      if (algorithmAck) frame(0x2e,{});
      return 0;
    }
    lastRequest=command;
    bool arrows=command==0x22 || command==0x25 || command==0x28;
    bool byId=command==0x27 || command==0x28;
    bool learned=command==0x24 || command==0x25;
    int id=byId ? tx[5] | (static_cast<int>(tx[6])<<8) : -1;
    std::vector<FakeResult> selected;
    for (const FakeResult& r: results) {
      if (r.command!=(arrows ? 0x2b : 0x2a)) continue;
      if (byId && r.id!=id) continue;
      if (learned && r.id<=0) continue;
      selected.push_back(r);
    }
    frame(0x29,{static_cast<int>(selected.size()),4,1}); // info
    for (const FakeResult& r: selected) frame(r.command,{r.first,r.second,r.third,r.fourth,r.id});
    return 0;
  }
  int requestFrom(int address, int count) {
    lastAddress=address;
    int sent=0;
    while (sent<count && !pending.empty()) {
      rx.push_back(pending.front()); pending.pop_front(); ++sent;
    }
    return sent;
  }
  int available() { return static_cast<int>(rx.size()); }
  int read() {
    if (rx.empty()) return -1;
    int value=rx.front(); rx.pop_front(); return value;
  }
};
extern TwoWire Wire;
