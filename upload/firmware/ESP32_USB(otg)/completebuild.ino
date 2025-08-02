#if ARDUINO_USB_MODE
#warning This sketch should be used when USB is in OTG mode

void setup() {}
void loop() {}

#else

#include "USB.h"
#include "USBMIDI.h"


// ==========================  POTENTIOMETER VARIABLES  ============================
const int N_POTS = 5;
int potPin[N_POTS] = { 7, 1, 2, 3, 4 };
int potCC[N_POTS] = { 24, 25, 26, 27, 7 };
int potChannel[N_POTS] = { 1, 1, 1, 1, 1 };
int ccMin[N_POTS] = { 24, 25, 26, 27, 7 };
int ccMax[N_POTS] = { 24, 25, 26, 27, 7 };

int potReading[N_POTS] = { 0 };
int potState[N_POTS] = { 0 };
int potPState[N_POTS] = { 0 };

int midiState[N_POTS] = { 0 };
int midiPState[N_POTS] = { 0 };
// =================================================================================

// ============================  JOYSTICK VARIABLES  ===============================
int joystick_y_axis[3] = { channel, pin, cc };
int joystickMax[N_JOYSTICK] = { 28, 29, 30, 31, 32 };
// =================================================================================

byte potThreshold = 15;
const int POT_TIMEOUT = 300;
unsigned long pPotTime[N_POTS] = { 0 };
unsigned long potTimer[N_POTS] = { 0 };

// Pitch Wheel Variables
int pitchReading = 0;
int pitchMidiState = 0;
int pitchMidiPState = 0;
int pitchState = 0;
int pitchPrevState = 0;
byte pitchThreshold = 3;
// =========================================================================


void setup() {
  USB.begin();
  usbmidi.begin();  // USB MIDI INSTANCE
}

void loop() {
  // ============  READ THROUGH ALL POTS MINUS PITCH AND MOD WHEELS  =====================
  for (int i = 0; i < N_POTS; i++) {
    potReading[i] = analogRead(potPin[i]);
    potState[i] = potReading[i];
    midiState[i] = map(potState[i], 0, 1023, ccMin[i], ccMax[i]);

    int potVar = abs(potState[i] - potPState[i]);

    if (potVar > potThreshold) {
      pPotTime[i] = millis();
    }

    potTimer[i] = millis() - pPotTime[i];

    if (potTimer[i] < POT_TIMEOUT) {
      if (midiState[i] != midiPState[i]) {
        uControlChange(potChannel[i], potCC[i], midiState[i]);
        midiPState[i] = midiState[i];
      }
      potPState[i] = potState[i];
    }
  }
  // ========================================================================================


  // // =============================  READ THE PITCH/MOD WHEEL  ==============================
  // mux3_ch(wheelStateButton);
  // wheelState = !digitalRead(signal3);

  // if (!wheelState) {
  //   mod_wheel();
  // } else {
  //   pitch_wheel();
  // }
  // // =======================================================================================
}


void uNoteOn(byte channel, byte note, byte velocity) {
  usbmidi.noteOn(note, velocity, channel);
}

void uNoteOff(byte channel, byte note, byte velocity) {
  usbmidi.noteOff(note, velocity, channel);
}

void uControlChange(byte channel, byte control, byte value) {
  usbmidi.controlChange(control, value, channel);
}

void uPitchBend(int16_t value, int channel) {
  usbmidi.pitchBend(value, channel);
}



// The generic "int" or "byte" data types cannot be used here to represent values greater than 256 ()
// this is because it comprises of just 8 bits, with a max possible permutation of 256 (2**8)
// Thus, we must explicitly specicy to use the 16 bits variant (int16_t or uint16_t) to represent
// a range of 0 - 16383 or -8192 to 8191. (2**14)

void mod_wheel() {

  // The Modulation Wheel has to be written separately,
  // because of the difference in the range of values
  // - 127 to 127, precisely.
  mux3_ch(modLockPin);
  modLock = !digitalRead(signal3);

  if (!modLock) {
    if (wheelState) {
      mux3_ch(wheelPin);
      int modReading = analogRead(signal3);
      modState = modReading;
      modMidiState = map(modReading, 0, 1023, -127, 127);
      int modVar = abs(modState - modPrevState);

      if (modVar > potThreshold) {
        pModTime = millis();
      }

      modTimer = millis() - pModTime;

      if (modTimer < POT_TIMEOUT) {
        if (modMidiState != modMidiPState) {
          if (modMidiState >= 0) {
            // Send Modulation coarse (CC 1)
            uControlChange(channel, 1, modMidiState);
          } else {
            // Send modulation LSB fine/smooth (CC 33)
            uControlChange(channel, 33, abs(modMidiState));
          }
          modMidiPState = modMidiState;
        }
        modPrevState = modState;
      }
    }
  }
}

void pitch_wheel() {

  mux3_ch(wheelPin);
  int pitchReading = analogRead(signal3);
  ;
  pitchState = pitchReading;
  pitchMidiState = map(pitchReading, 1023, 0, 0, 16383);

  int pitchVar = abs(pitchState - pitchPrevState);

  if (pitchVar > pitchThreshold) {

    if (pitchMidiState != pitchMidiPState) {
      uPitchBend(pitchMidiState, channel);
      pitchPrevState = pitchState;
      // delay(5);
    }
    pitchMidiPState = pitchMidiState;
  }
}

#endif /* ARDUINO_USB_MODE */