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

def installed_boards():
    try:
        result = subprocess.run(
            ["arduino-cli", "board", "listall"],
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

    # Generate knob, button, joystick arrays
    firmware_string += fl.knobs_buttons_joystick(preset)

    
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
    firmware_string = "#include <MIDIUSB.h>\n"
    firmware_string += fl.knobs_buttons_joystick(preset)
    firmware_string += fl.avr['setup']
    firmware_string += fl.avr['loop']
    firmware_string += fl.avr['functions']

    print('\n\n\n')
    print(firmware_string)

    return firmware_string


def generate_pico_firmware(preset, modes_string):
    firmware_string = ""
    modes = modes_string.split('+')
    
    print(f'the modes are: {modes}')
    
    return firmware_string


def generate_stm_firmware(preset, modes_string):
    firmware_string = ""
    modes = modes_string.split('+')

    print(f'the modes are: {modes}')

    return firmware_string

