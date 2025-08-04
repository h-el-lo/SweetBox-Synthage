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






avr = {
  'setup': '''
void setup() {

}''',

  'loop': '''
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
          // Starts with 0 (channel 1)
          controlChange(potChannel[i] - 1, potCC[i], midiState[i]);
          midiPState[i] = midiState[i];
        }
        potPState[i] = potState[i];
      }
    }
}
''',

  'functions': '''
void noteOn(byte channel, byte note, byte velocity) {
  midiEventPacket_t event = { 0x09, 0x90 | channel, note, velocity };
  MidiUSB.sendMIDI(event);
  MidiUSB.flush();
}

void noteOff(byte channel, byte note, byte velocity) {
  midiEventPacket_t noteOff = { 0x08, 0x80 | channel, note, velocity };
  MidiUSB.sendMIDI(noteOff);
  MidiUSB.flush();
}

void controlChange(byte channel, byte control, byte value) {
  midiEventPacket_t event = { 0x0B, 0xB0 | channel, control, value };
  MidiUSB.sendMIDI(event);
  MidiUSB.flush();
}

void pitchBend(byte channel, int value) {
  midiEventPacket_t pitchBend = { 0x0E, 0xE0 | channel, value & 0x7F, (value >> 7) & 0x7F };
  MidiUSB.sendMIDI(pitchBend);
  MidiUSB.flush();
}''',
}


def knobs_buttons_joystick(preset):
    knob_count = len(preset.knob_set.all())
    knobs = preset.knob_set.all()
    # button_count = len(preset.button_set.all())
    # buttons = preset.button_set.all()
    joystick = preset.joystick_set.all()[0] if preset.joystick_set.all() else None
    firmware_string = ""

    # Knobs/Sliders Section
    firmware_string += f"\n\n// ==========================  POTENTIOMETER VARIABLES  ===========================\n"
    if knob_count > 0:
        firmware_string += f"const int N_POTS = {knob_count};\n"

        firmware_string += f"int potPin[N_POTS] = {{ "
        for knob in preset.knob_set.all():
            firmware_string += f"{knob.pin}, "
        firmware_string += f"}};\n"

        firmware_string += f"int potCC[N_POTS] = {{ "
        for knob in preset.knob_set.all():
            firmware_string += f"{knob.CC}, "
        firmware_string += f"}};\n"

        firmware_string += f"int potChannel[N_POTS] = {{ "
        for knob in preset.knob_set.all():
            firmware_string += f"{knob.channel}, "
        firmware_string += f"}};\n"

        firmware_string += f"int ccMin[N_POTS] = {{ "
        for knob in preset.knob_set.all():
            firmware_string += f"{knob.min}, "
        firmware_string += f"}};\n"

        firmware_string += f"int ccMax[N_POTS] = {{ "
        for knob in preset.knob_set.all():
            firmware_string += f"{knob.max}, "
        firmware_string += f"}};\n"

        firmware_string += f'''

// ==========================  POTENTIOMETER VARIABLES  ===========================
const int N_POTS = {{{knob_count}}};
int potPin[N_POTS] = {{ {knob.pin for knob in knobs} }};



int potReading[N_POTS] = { 0 };
int potState[N_POTS] = { 0 };
int potPState[N_POTS] = { 0 };

int midiState[N_POTS] = { 0 };
int midiPState[N_POTS] = { 0 };

byte potThreshold = 15;
const int POT_TIMEOUT = 300;
unsigned long pPotTime[N_POTS] = { 0 };
unsigned long potTimer[N_POTS] = { 0 };
// =================================================================================


'''
    else:
        firmware_string += f"// ==========================  POTENTIOMETER VARIABLES  ===========================\n"
        firmware_string += '''const int N_POTS = 0;
int potPin[N_POTS] = { 0 };
int potCC[N_POTS] = { 0 };
int potChannel[N_POTS] = { 0 };
int ccMin[N_POTS] = { 0 };
int ccMax[N_POTS] = { 0 };

int potReading[N_POTS] = { 0 };
int potState[N_POTS] = { 0 };
int potPState[N_POTS] = { 0 };

int midiState[N_POTS] = { 0 };
int midiPState[N_POTS] = { 0 };

byte potThreshold = 15;
const int POT_TIMEOUT = 300;
unsigned long pPotTime[N_POTS] = { 0 };
unsigned long potTimer[N_POTS] = { 0 };'''
        firmware_string += f"// =================================================================================\n\n"

    # Joystick Section
    if joystick:
        firmware_string += f"// ===========================  JOYSTICK VARIABLES  ================================\n"
        firmware_string += f"int joystick_y_axis[3] = {{ {joystick.y_channel}, {joystick.y_pin}, {joystick.y_cc} }};\n"
        if joystick.x_mode == 'cc':
            firmware_string += f"int joystick_x_axis[3] = {{ {joystick.x_channel}, {joystick.x_pin}, {joystick.x_cc} }};\n"
            firmware_string += f"// =================================================================================\n"
        else:
            firmware_string += f"// =================================================================================\n\n"
            # firmware_string += f"// ==========================  PITCH VARIABLES  ===============================\n"
            # firmware_string += f"int pitchPin = {joystick.x_pin};\n"
            # firmware_string += f"int pitchCC = {joystick.x_cc};\n"
            # firmware_string += f"int pitchChannel = {joystick.x_channel};\n"
            # firmware_string += f"int pitchState = 0;\n"
            # firmware_string += f"// =================================================================================\n\n"

    
    return firmware_string