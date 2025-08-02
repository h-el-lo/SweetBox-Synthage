libs = {
    'USB (OTG)': '''
#include "USB.h"
#include "USBMIDI.h"
''',
    'BLE': '''
#include <BLEMIDI_Transport.h>
#include <hardware/BLEMIDI_ESP32.h>
''',
}

libs_init = {
    'USB (OTG)':'''
USBMIDI usbmidi;''',
    'BLE': '''
BLEMIDI_CREATE_INSTANCE("SweetBox-Synthage", MIDI);'''
}

libs_setup = {
    'USB (OTG)': '''
  USB.begin();
  usbmidi.begin();  // USB MIDI INSTANCE''',
    'BLE': '''
  MIDI.begin();  // BLE MIDI INSTANCE''',
    }

libs_controls = {
    'USB (OTG)': '''
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
''',
    'BLE': '''
void bNoteOn(byte channel, byte note, byte velocity) {
  MIDI.sendNoteOn(note, velocity, channel);
}

void bNoteOff(byte channel, byte note, byte velocity) {
  MIDI.sendNoteOff(note, velocity, channel);
}

void bControlChange(byte channel, byte control, byte value) {
  MIDI.sendControlChange(control, value, channel);
}

void bPitchBend(byte channel, int value) {
  MIDI.sendPitchBend(value, channel);
}
''',
}

libs_loop = {
  'USB (OTG)': '''
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
}
''',

  'BLE': '''
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
          bControlChange(potChannel[i], potCC[i], midiState[i]);
          midiPState[i] = midiState[i];
        }
        potPState[i] = potState[i];
      }
    }
}
''', 
}