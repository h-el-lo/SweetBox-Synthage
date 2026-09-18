# utils/arduino.py
import subprocess, os, uuid, json
from django.conf import settings
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

def get_cores():
    try:
        with open(os.path.join(settings.BASE_DIR, 'upload', 'boards.json'), 'r') as f:
            cores = json.load(f)
    except json.JSONDecodeError:
        print('JSON decode error')
        cores = []
    except FileNotFoundError:
        cores = []
    return cores

def create_work_sketch_dir(preset, firmware_string):
    # Create work directory and sketch directory
    uid = uuid.uuid4().hex[:8]
    work_dir = os.path.join(settings.MEDIA_ROOT, uid)
    os.makedirs(work_dir, exist_ok=True)
    
    # Create sketch directory with preset name
    sketch_name = f"preset_{preset.id}_{preset.name.replace(' ', '_')}"
    sketch_dir = os.path.join(work_dir, sketch_name)
    os.makedirs(sketch_dir, exist_ok=True)
    
    # Save firmware to .ino file
    sketch_path = os.path.join(sketch_dir, f"{sketch_name}.ino")
    with open(sketch_path, 'w') as f:
        f.write(firmware_string)

    return work_dir, sketch_dir, uid

def compile_command(sketch_path, fqbn):

    command = [
        "arduino-cli",
        "compile",
        "--fqbn", fqbn,
        sketch_path
    ]

    result = subprocess.run(command, capture_output=True, text=True, env=env)

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def generate_esp_firmware(preset, modes_string):
    firmware_string = ""
    modes = modes_string.split('+')

    if 'USB (OTG)' in modes_string:
        firmware_string += fl.OTG_WARNING
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
        firmware_string += fl.OTG_END

    print(firmware_string)
    return firmware_string

def generate_avr_firmware(preset):
    firmware_string = "#include <MIDIUSB.h>\n"
    firmware_string += fl.knobs_buttons_joystick(preset)
    firmware_string += fl.avr['setup']
    firmware_string += fl.avr['loop']
    firmware_string += fl.avr['functions']

    print('\n\n\n')
    print(firmware_string)

    return firmware_string

def generate_pico_firmware(preset):
    firmware_string = "#include <Adafruit_TinyUSB_MIDI.h>\n\n"
    firmware_string += "Adafruit_TinyUSB_MIDI MIDI;\n\n"
    firmware_string += fl.knobs_buttons_joystick(preset)
    firmware_string += fl.pico['setup']
    firmware_string += fl.pico['loop']
    firmware_string += fl.pico['functions']

    print('\n\n\n')
    print(firmware_string)

    return firmware_string

def generate_stm_firmware(preset):
    firmware_string = "#include <USBComposite.h>\n\n"
    firmware_string += "USBMIDI MIDI;\n\n"
    firmware_string += fl.knobs_buttons_joystick(preset)
    firmware_string += fl.stm['setup']
    firmware_string += fl.stm['loop']
    firmware_string += fl.stm['functions']

    print('\n\n\n')
    print(firmware_string)

    return firmware_string

