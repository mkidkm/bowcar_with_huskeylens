// Test generated startup mode selection against the framed I2C simulator.
// Compile with BC_SKETCH and BC_ALGORITHM; run one scenario per process.
#include <cassert>
#include <iostream>
#include <string>
#include "Arduino.h"
#include "Wire.h"

unsigned long fakeClock=0;
int fakePwm[32]={0}, fakeDigital[32]={0};
Stream Serial;
TwoWire Wire;
#include BC_SKETCH

static void stopped() { assert(fakePwm[5]==0 && fakePwm[6]==0); }

int main(int argc, char** argv) {
  assert(argc==2);
  const std::string scenario=argv[1];
  assert(scenario=="ready" || scenario=="camera_late" || scenario=="ack_failed");
  if (scenario=="camera_late") Wire.cameraAlive=false;
  if (scenario=="ack_failed") Wire.algorithmAck=false;

  setup();
  stopped();
  assert(!bc_found && Wire.requestCount==0);

  if (scenario=="ready") {
    // Select the mode before any target request, once per stable connection.
    assert(bc_connected && Wire.lastAlgorithm==BC_ALGORITHM);
    assert(Wire.algorithmCount==1);
    loop(); loop();
    stopped();
    assert(Wire.algorithmCount==1 && Wire.requestCount==2);

    Wire.results={{0x2a,160,120,40,30,1}};
    loop();
    assert(bc_found && Wire.algorithmCount==1);
    Wire.cameraAlive=false;
    loop();
    stopped();
    assert(!bc_connected && !bc_found);

    // Reconnection must set the program's mode again before using targets.
    Wire.cameraAlive=true;
    fakeClock+=1001;
    loop();
    assert(bc_connected && bc_found && Wire.lastAlgorithm==BC_ALGORITHM);
    assert(Wire.algorithmCount==2);
  } else {
    // A missing camera or missing mode ACK must not permit target use or motion.
    assert(!bc_connected && !bc_found);
    assert(Wire.algorithmCount==(scenario=="ack_failed" ? 1 : 0));
    const int algorithms=Wire.algorithmCount;
    const int knocks=Wire.knockCount;
    bc_motor(100,100);
    stopped();
    loop();
    stopped();
    assert(!bc_connected && Wire.requestCount==0);
    assert(Wire.algorithmCount==algorithms && Wire.knockCount==knocks);

    Wire.cameraAlive=true;
    Wire.algorithmAck=true;
    Wire.results={{0x2a,160,120,40,30,1}};
    fakeClock+=1001;
    loop();
    assert(bc_connected && bc_found && Wire.lastAlgorithm==BC_ALGORITHM);
    assert(Wire.algorithmCount==algorithms+1 && Wire.requestCount==1);
  }

  assert(Wire.lastRequest==BC_REQUEST && Wire.lastAddress==0x32);
  std::cout << "PASS algorithm=" << BC_ALGORITHM << " scenario=" << scenario << "\n";
}
