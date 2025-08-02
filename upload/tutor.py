def generate_firmware(preset, functions_string):
    firmware_string = ""

    libs = {
        'usb (otg)': '''
#include "USB.h"
#include "USBMIDI.h"
''',
    }

    libs_setup = {
        'usb (otg)': '''
  USB.begin();
  usbmidi.begin();''',
    }
    
    knob_count = len(preset.knobs.all())
    button_count = len(preset.buttons.all())
    joystick = preset.joystick.all()[0] if preset.joystick.all() else None

    # Knobs/Sliders Section
    firmware_string += f"// ==========================  POTENTIOMETER VARIABLES  ===========================\n"
    if knob_count > 0:
        firmware_string += f"const int N_POTS = {knob_count};\n"

        firmware_string += f"int potPin[N_POTS] = {{ "
        for knob in preset.knobs.all():
            firmware_string += f"{knob.pin}, "
        firmware_string += f" }};\n"

        firmware_string += f"int potCC[N_POTS] = {{"
        for knob in preset.knobs.all():
            firmware_string += f"{knob.CC}, "
        firmware_string += f"}};\n"

        firmware_string += f"int potChannel[N_POTS] = {{"
        for knob in preset.knobs.all():
            firmware_string += f"{knob.channel}, "
        firmware_string += f"}};\n"

        firmware_string += f"int ccMin[N_POTS] = {{"
        for knob in preset.knobs.all():
            firmware_string += f"{knob.cc_min}, "
        firmware_string += f"}};\n"

        firmware_string += f"int ccMax[N_POTS] = {{"
        for knob in preset.knobs.all():
            firmware_string += f"{knob.cc_max}, "
        firmware_string += f"}};\n"

        firmware_string += '''
int potReading[N_POTS] = { 0 };
int potState[N_POTS] = { 0 };
int potPState[N_POTS] = { 0 };

int midiState[N_POTS] = { 0 };
int midiPState[N_POTS] = { 0 };
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
int midiPState[N_POTS] = { 0 };'''
        firmware_string += f"// =================================================================================\n\n"

    # Joystick Section
    if joystick:
        firmware_string += f"// ==========================  JOYSTICK VARIABLES  ===============================\n"
        firmware_string += f"int joystick_y_axis[3] = {{ {joystick.y_channel}, {joystick.y_pin}, {joystick.y_cc} }};\n"
        if joystick.x_mode == 'cc':
            firmware_string += f"int joystick_x_axis[3] = {{ {joystick.x_axis.channel}, {joystick.x_axis.pin}, {joystick.x_axis.cc} }};\n"
            firmware_string += f"// =================================================================================\n"
        else:
            firmware_string += f"// =================================================================================\n\n"
            # firmware_string += f"// ==========================  PITCH VARIABLES  ===============================\n"
            # firmware_string += f"int pitchPin = {joystick.x_pin};\n"
            # firmware_string += f"int pitchCC = {joystick.x_cc};\n"
            # firmware_string += f"int pitchChannel = {joystick.x_channel};\n"
            # firmware_string += f"int pitchState = 0;\n"
            # firmware_string += f"// =================================================================================\n\n"

    firmware_string += f"setup() {{\n"
    firmware_string += f"  {libs_setup[preset.firmware_type]}\n"
    firmware_string += f"}}\n"


    return firmware_string