# utils/arduino.py
import subprocess, os
from . import firmware_libs as fl

def check_installed():
    """
    Checks if arduino-cli is installed and available in the system PATH.

    Returns:
        tuple: (is_installed (bool), message (str))
    """
    try:
        result = subprocess.run(
            ["arduino-cli", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except FileNotFoundError:
        return False, "arduino-cli is not found. Please install it and ensure it is in your PATH."
    except subprocess.CalledProcessError as e:
        return False, f"Error executing arduino-cli: {e.stderr.strip() if e.stderr else 'Unknown error'}"



def generate_esp_firmware(preset, modes_string):
    firmware_string = ""
    modes = modes_string.split('+')
    
    knob_count = len(preset.knob_set.all())
    # button_count = len(preset.button_set.all())
    joystick = preset.joystick_set.all()[0] if preset.joystick_set.all() else None

    print(modes_string, '\n\n\n\n\n')
    print(preset)

    if 'USB (OTG)' in modes_string:
        firmware_string += '''
#if ARDUINO_USB_MODE
#warning This sketch should be used when USB is in OTG mode

void setup() {}
void loop() {}

#else
'''
    for mode in modes:
        firmware_string += fl.libs[mode]
    for mode in modes:
        firmware_string += fl.libs_init[mode]

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

    print(f'the modes are: {modes}')

    # Write the setup function
    firmware_string += f"void setup() {{\n"
    for mode in modes:
        firmware_string += f"  {fl.libs_setup[mode]}\n"

    firmware_string += f"}}\n"

    firmware_string += fl.libs_loop[modes[0]]
    firmware_string += '\n\n'

    for mode in modes:
        firmware_string += fl.libs_controls[mode]

    if 'USB (OTG)' in modes:
        firmware_string += "\n#endif"

    print(firmware_string)
    return firmware_string


    

def generate_avr_firmware(preset, modes_string):
    firmware_string = ""
    modes = modes_string.split('+')

    print(modes_string, '\n\n\n\n\n')
    print(preset)

    return firmware_string