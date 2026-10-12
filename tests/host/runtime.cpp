// Compile with -DBC_SKETCH="absolute/sketch.ino" and -DBC_TEST=N.
#include <cassert>
#include <iostream>
#include "Arduino.h"
#include "Wire.h"
unsigned long fakeClock=0;
int fakePwm[32]={0}, fakeDigital[32]={0};
Stream Serial;
TwoWire Wire;
#include BC_SKETCH

static void stopped() { assert(fakePwm[5]==0 && fakePwm[6]==0); }
static void speeds(int left,int right) { assert(fakePwm[5]==left && fakePwm[6]==right); }
static FakeResult block(int x, int width=40, int id=1) { return {0x2a,x,120,width,30,id}; }
static FakeResult arrow(int x, int id=1) { return {0x2b,160,200,x,60,id}; }

int main() {
  setup();
  stopped();
  assert(Wire.timeout==25000UL);
#if BC_TEST == 1
  Wire.results={block(160)};
  loop();
  assert(bc_connected && bc_found && bc_id==1);
  stopped();
  Wire.results.clear(); loop();
  assert(bc_connected && !bc_found && bc_id==0 && bc_x==0 && bc_width==0);
  stopped();
#elif BC_TEST == 2
  Wire.results={block(160)}; loop(); speeds(100,100);
  Wire.results={block(80)}; loop(); speeds(55,145);
  Wire.results={block(240)}; loop(); speeds(145,55);
  Wire.results={block(160,100)}; loop(); stopped();
  Wire.results={block(160,40,2)}; loop(); stopped(); assert(!bc_found);
  Wire.results={block(160)}; loop();
  bc_motor(9999,-9999); speeds(255,255);
  assert(fakeDigital[2]==LOW && fakeDigital[4]==HIGH);
  bc_delay(500); stopped();
  Wire.results={block(240,50),block(160,120)}; loop();
  assert(bc_width==120); stopped(); // largest area is selected
  Wire.results={block(160)}; loop(); speeds(100,100);
  Wire.results.clear(); loop(); stopped(); assert(!bc_found && bc_x==0);
  Wire.results={block(160)}; loop(); speeds(100,100);
  Wire.cameraAlive=false; loop(); stopped(); assert(!bc_connected && !bc_found);
  Wire.cameraAlive=true; loop(); stopped(); assert(!bc_connected); // retry backoff
  fakeClock+=1001; loop(); speeds(100,100); assert(bc_connected);
  Wire.cameraAlive=false; loop(); stopped();
  Wire.cameraAlive=true; Wire.algorithmAck=false; fakeClock+=1001; loop();
  stopped(); assert(!bc_connected); // failed algorithm acknowledgement
  Wire.algorithmAck=true; fakeClock+=1001; loop(); speeds(100,100);
  assert(Wire.lastAlgorithm==ALGORITHM_OBJECT_TRACKING && Wire.lastRequest==0x27);
#elif BC_TEST == 3
  Wire.results={block(160,40,2)}; loop(); speeds(90,90);
  assert(fakeDigital[2]==HIGH && fakeDigital[4]==LOW);
  Wire.results={block(160,40,3)}; loop(); speeds(90,90);
  assert(fakeDigital[2]==LOW && fakeDigital[4]==HIGH);
  Wire.results={block(160,40,4)}; loop(); speeds(90,90);
  assert(fakeDigital[2]==LOW && fakeDigital[4]==LOW);
  Wire.results={block(160,100,4),block(160,10,1)}; loop(); stopped(); assert(bc_id==1);
  Wire.results={block(160,40,0)}; loop(); stopped(); assert(!bc_found);
  Wire.results={block(160,40,5)}; loop(); stopped();
  assert(Wire.lastAlgorithm==ALGORITHM_TAG_RECOGNITION && Wire.lastRequest==0x24);
#elif BC_TEST == 4
  Wire.results={arrow(160)}; loop(); speeds(90,90);
  Wire.results={arrow(240)}; loop(); speeds(130,50);
  Wire.results={arrow(80)}; loop(); speeds(50,130);
  Wire.results={arrow(160,2)}; loop(); stopped(); assert(!bc_found);
  Wire.results={arrow(400)}; loop(); stopped(); assert(!bc_found);
  Wire.results.clear(); loop(); stopped(); assert(bc_xTarget==0);
  assert(Wire.lastAlgorithm==ALGORITHM_LINE_TRACKING && Wire.lastRequest==0x28);
#endif
  assert(Wire.lastAddress==0x32);
  std::cout << "PASS " << BC_TEST << "\n";
}
