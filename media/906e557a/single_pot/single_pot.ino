// #ifndef ARDUINO_USB_MODE
// #define ARDUINO_USB_MODE 0
// #endif

#if ARDUINO_USB_MODE
#warning This sketch should be used when USB is in OTG mode

void setup() {}
void loop() {}

#else

#include "USB.h"
#include "USBMIDI.h"

// #include <BLEMIDI_Transport.h>
// #include <hardware/BLEMIDI_ESP32.h>

// ============================  MIDI VARIABLES  =============================
const int channel = 2;
// BLEMIDI_CREATE_INSTANCE("Annihilō", MIDI);
USBMIDI usbmidi;
// ==========================================================


// ===================  POTENTIOMETER VARIABLES  =======================
const int pot = 13;
int potReading;


void setup() {
  // put your setup code here, to run once:
  // MIDI.begin();  // BLE MIDI INSTANCE
  USB.begin();
  usbmidi.begin();  // USB MIDI INSTANCE
}

void loop() {

  // ============  READ THROUGH ALL POTS MINUS PITCH AND MOD WHEELS  =====================
  potReading = map(analogRead(pot), 0, 1023, 0, 127);
  // bControlChange(channel, 7, potReading);
  uControlChange(channel, 7, potReading);
  // ========================================================================================
}

// void bNoteOn(byte channel, byte note, byte velocity) {
//   MIDI.sendNoteOn(note, velocity, channel);
// }

// void bNoteOff(byte channel, byte note, byte velocity) {
//   MIDI.sendNoteOff(note, velocity, channel);
// }

// void bControlChange(byte channel, byte control, byte value) {
//   MIDI.sendControlChange(control, value, channel);
// }

// void bPitchBend(byte channel, int value) {
//   MIDI.sendPitchBend(value, channel);
// }

void uNoteOn(byte channel, byte note, byte velocity) {
  usbmidi.noteOn(note, velocity, channel);
}

void uNoteOff(byte channel, byte note, byte velocity) {
  usbmidi.noteOff(note, velocity, channel);
}

void uControlChange(byte channel, byte control, byte value) {
  usbmidi.controlChange(control, value, channel);
}

// The generic "int" or "byte" data types cannot be used here to represent values greater than 256 ()
// this is because it comprises of just 8 bits, with a max possible permutation of 256 (2**8)
// Thus, we must explicitly specicy to use the 16 bits variant (int16_t or uint16_t) to represent
// a range of 0 - 16383 or -8192 to 8191. (2**14)
void uPitchBend(int16_t value, int channel) {
  usbmidi.pitchBend(value, channel);
}


#endif /* ARUDINO_USB_MODE*/