// Execute the actual generated sketch with deterministic clock and sensor inputs.
#include <cassert>
#include <iostream>
#include "Arduino.h"

unsigned long fakeClock=0, fakeEchoUs=0;
int fakePwm[32]={0}, fakeDigital[32]={0}, fakeInputs[32], fakeAnalog[32]={0};
std::vector<OutputEvent> outputEvents;
std::vector<LogEvent> logEvents;
std::vector<EchoEvent> echoEvents;
Stream Serial;
#include TC_SKETCH

#ifndef TC_SPEED
#define TC_SPEED 100
#endif
#ifndef TC_THRESHOLD
#define TC_THRESHOLD 500
#endif
#ifndef TC_STOP_CM
#define TC_STOP_CM 20
#endif

static void stopped() { assert(fakePwm[LM_PWM_PIN]==0 && fakePwm[RM_PWM_PIN]==0); }
static void lights(int red,int blue) {
  stopped();
  assert(fakeDigital[RED_LED_PIN]==red && fakeDigital[BLUE_LED_PIN]==blue);
}
static int boots() {
  int count=0;
  for (const LogEvent& entry: logEvents) if (entry.text=="BOOT") ++count;
  return count;
}
static bool motorPin(const OutputEvent& event) {
  return event.pin==LM_PWM_PIN || event.pin==RM_PWM_PIN ||
         event.pin==LM_DIR_PIN || event.pin==RM_DIR_PIN;
}
static void zeroOnly(unsigned long start,unsigned long end) {
  int left=0,right=0;
  size_t index=0;
  while (index<outputEvents.size() && outputEvents[index].time<end) {
    const unsigned long time=outputEvents[index].time;
    // Pin writes at the same fake ms are one observation, not elapsed motion.
    while (index<outputEvents.size() && outputEvents[index].time==time) {
      const OutputEvent& event=outputEvents[index++];
      if (event.pwm && event.pin==LM_PWM_PIN) left=event.value;
      if (event.pwm && event.pin==RM_PWM_PIN) right=event.value;
    }
    const unsigned long next=index<outputEvents.size() ? outputEvents[index].time : end;
    if (next>start) assert(left==0 && right==0);
  }
  assert(left==0 && right==0);
}
static void held(unsigned long start,unsigned long end,int left,int right) {
  int lp=0,rp=0,ld=0,rd=0;
  bool activeAtStart=false;
  for (const OutputEvent& event: outputEvents) {
    if (event.time>=end) break;
    if (event.pwm && event.pin==LM_PWM_PIN) lp=event.value;
    if (event.pwm && event.pin==RM_PWM_PIN) rp=event.value;
    if (!event.pwm && event.pin==LM_DIR_PIN) ld=event.value;
    if (!event.pwm && event.pin==RM_DIR_PIN) rd=event.value;
    if (event.time==start && event.pwm && event.value>0) activeAtStart=true;
    if (event.time>start && motorPin(event)) assert(false); // No shortened/interrupted stage.
  }
  assert(activeAtStart && lp==std::abs(left) && rp==std::abs(right));
  assert(ld==(left<0 ? HIGH : LOW) && rd==(right<0 ? HIGH : LOW));
}
static void basicCycle() {
  const unsigned long start=fakeClock;
  const size_t firstLog=logEvents.size();
  loop();
  assert(fakeClock-start==6200UL);
  assert(logEvents.size()-firstLog==10);
  const char* names[]={"FORWARD","BACKWARD","LEFT","RIGHT","STOP"};
  const int left[]={TC_SPEED,-TC_SPEED,-TC_SPEED,TC_SPEED,0};
  const int right[]={TC_SPEED,-TC_SPEED,TC_SPEED,-TC_SPEED,0};
  const unsigned long dwell[]={1000,1000,500,500,2000};
  unsigned long previous=start;
  for (int i=0;i<5;++i) {
    const LogEvent& step=logEvents[firstLog+i*2];
    const LogEvent& done=logEvents[firstLog+i*2+1];
    assert(step.text.find(std::string("STEP,")+names[i]+",")==0);
    assert(done.text.find(std::string("DONE,")+names[i]+",")==0);
    assert(step.time-previous==(i<4 ? 300UL : 0UL));
    assert(done.time-step.time==dwell[i]);
    if (i<4) {
      zeroOnly(previous,step.time);
      held(step.time,done.time,left[i]*TC_LEFT,right[i]*TC_RIGHT);
    } else zeroOnly(step.time,done.time);
    previous=done.time;
  }
  stopped();
}

int main() {
  std::fill(fakeInputs,fakeInputs+32,HIGH);
  setup();
  stopped();
  assert(fakeClock==600UL && boots()==1);
  zeroOnly(0,fakeClock+1);
#if TC_CASE == 1
  basicCycle();
  basicCycle(); // All stages repeat without a second BOOT.
#elif TC_CASE == 2
  loop(); lights(LOW,LOW);
  fakeInputs[DB_PIN]=LOW; loop(); lights(HIGH,LOW);
  fakeInputs[DB_PIN]=HIGH; fakeInputs[UB_PIN]=LOW; loop(); lights(LOW,HIGH);
  fakeInputs[DB_PIN]=LOW; loop(); lights(HIGH,HIGH);
#elif TC_CASE == 3
  fakeAnalog[LS_PIN]=TC_THRESHOLD-1; loop(); lights(HIGH,LOW);
  fakeAnalog[LS_PIN]=TC_THRESHOLD; loop(); lights(LOW,HIGH);
  fakeAnalog[LS_PIN]=TC_THRESHOLD+1; loop(); lights(LOW,HIGH);
#elif TC_CASE == 4
  fakeAnalog[SS_PIN]=TC_THRESHOLD-1; loop(); lights(HIGH,LOW);
  fakeAnalog[SS_PIN]=TC_THRESHOLD; loop(); lights(HIGH,LOW);
  fakeAnalog[SS_PIN]=TC_THRESHOLD+1; loop(); lights(LOW,HIGH);
#elif TC_CASE == 5
  fakeAnalog[IRL_PIN]=TC_THRESHOLD-1; fakeAnalog[IRR_PIN]=TC_THRESHOLD+1;
  loop(); lights(HIGH,LOW);
  fakeAnalog[IRL_PIN]=TC_THRESHOLD+1; fakeAnalog[IRR_PIN]=TC_THRESHOLD-1;
  loop(); lights(LOW,HIGH);
  fakeAnalog[IRL_PIN]=fakeAnalog[IRR_PIN]=TC_THRESHOLD;
  loop(); lights(LOW,LOW);
#elif TC_CASE == 6
  // A previous forward output must already be stopped when the next echo starts.
  const unsigned long echoes[]={(TC_STOP_CM+10)*58UL,0,TC_STOP_CM*58UL,
                                (TC_STOP_CM+10)*58UL};
  for (int i=0;i<4;++i) {
    fakeEchoUs=echoes[i];
    const unsigned long start=fakeClock;
    loop();
    assert(fakeClock-start>=100UL && fakeClock-start<=125UL);
    if (i==0 || i==3) {
      assert(fakePwm[LM_PWM_PIN]>0 && fakePwm[RM_PWM_PIN]>0);
      assert(fakeDigital[RED_LED_PIN]==LOW && fakeDigital[BLUE_LED_PIN]==HIGH);
    } else lights(HIGH,LOW);
  }
  assert(echoEvents.size()==4);
  for (const EchoEvent& event: echoEvents)
    assert(event.timeout==25000UL && event.left==0 && event.right==0);
#elif TC_CASE == 7
  for (int i=0;i<2;++i) {
    const unsigned long start=fakeClock;
    loop(); stopped();
    assert(fakeClock-start==1000UL);
  }
  int idleLogs=0;
  for (const LogEvent& entry: logEvents) if (entry.text.find("IDLE,")==0) ++idleLogs;
  assert(idleLogs==2);
#endif
  assert(boots()==1);
#if TC_CASE >= 2 && TC_CASE <= 5 || TC_CASE == 7
  zeroOnly(0,fakeClock+1);
  if (TC_CASE!=7) assert(logEvents.back().text.find("ms=")==0);
#endif
  std::cout<<"PASS teaching case="<<TC_CASE<<" polarity="<<TC_LEFT<<","<<TC_RIGHT<<"\n";
}
