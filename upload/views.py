# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

# Core Django utilities
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from presets.models import Preset, Knob, Button
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json, os, subprocess, uuid
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from base.models import Profile
from .utils import arduino
# Create your views here.


@login_required(login_url='/login/')
def download_firmware(request, preset_id):
    firmware_dir = os.path.join(settings.BASE_DIR, 'generated_firmware')
    firmware_path = os.path.join(firmware_dir, f'firmware_preset_{preset_id}.ino')
    if os.path.exists(firmware_path):
        return FileResponse(open(firmware_path, 'rb'), as_attachment=True, filename=f'firmware_preset_{preset_id}.ino')
    return redirect(reverse('portal'))


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

def get_boards_context(request):
    cores = get_cores()  # List of dicts like [{"ATmega32U4": [...]}, {"RP2040": [...]}]
    mcus = []
    # This list cannot be named "boards", it would otherwise cause an infinite loop in the subsequent "for" loop
    board_list = []
    for core in cores:
        for mcu, boards in core.items():
            mcus.append(mcu)
            for board in boards:
                board_list.append(board)

    midi_modes = set([ mode for mode in board['midi_modes'] for board in board_list])
    
    # Debug: Print the context data
    print(f"Available MCUs: {mcus}")
    print(f"Available boards: {[board['board'] for board in board_list]}")
    print(f"Board MCUs: {[board['mcu'] for board in board_list]}")
    
    context = {
        'cores': cores,
        'mcus': sorted(mcus),
        'midi_modes': midi_modes,
        'boards': board_list,
        'presets': Preset.objects.filter(owner=request.user),
        'hide_upload_link':True,
    }

    return context


@login_required(login_url='login')
def selection(request):
    context = get_boards_context(request)
    return render(request, 'upload/selection.html', context)

def sorter(request):
    if request.method == 'POST':
        mcu = request.POST.get('mcu')
        print(f"Sorter received MCU: {mcu}")
        if mcu and mcu.lower() == 'esp32':
            print(f"Routing to esp_upload for MCU: {mcu}")
            return esp_upload(request)
        # elif request.POST.get('mcu').lower() == 'atmega32u4':
        #     return generate_firmware(request)
        # elif request.POST.get('mcu').lower() == 'rp2040':
        #     return generate_firmware(request)
        else:
            print(f"Redirecting to selection for MCU: {mcu}")
            return redirect('selection')
    else:
        return redirect('selection')

def generate_firmware(preset, firmware_type):
    pass

def upload(request):
    context = {} 
    return render (request, 'upload/upload.html', context)

def arduino_cli_check(request):
    is_installed, message = arduino.check_installed()
    # context = {
    #     "is_installed": is_installed,
    #     "message": message,
    # }
    
    if is_installed:
        return HttpResponse(f'<p style="color: green;">✅ Installed: { message }</p>')
    else:
        return HttpResponse(f'<p style="color: red;">❌ Not Installed: { message }</p>')

from .forms import SketchUploadForm
def upload_sketch(request):
    form = SketchUploadForm()
    return render(request, 'upload/input.html', {'form': form})

def esp_upload(request):
    if request.method == 'POST':
        # Check if we have a custom firmware file
        if request.POST.get('firmware_type') == 'custom':
            if 'custom_firmware_file' not in request.FILES:
                return render(request, 'upload/esp_upload.html', {
                    'error': 'No custom firmware file was uploaded. Please select a .ino file.'
                })
            
            sketch_file = request.FILES['custom_firmware_file']
            uid = uuid.uuid4().hex[:8]
            work_dir = os.path.join(settings.MEDIA_ROOT, uid)
            os.makedirs(work_dir, exist_ok=True)

            sketch_name = os.path.splitext(sketch_file.name)[0]
            sketch_dir = os.path.join(work_dir, sketch_name)
            os.makedirs(sketch_dir, exist_ok=True)

            sketch_path = os.path.join(sketch_dir, sketch_file.name)
            with open(sketch_path, 'wb+') as dest:
                for chunk in sketch_file.chunks():
                    dest.write(chunk)

            context = get_boards_context(request)
            board_fqbn = None
            selected_board = request.POST.get('board') or request.POST.get('board_hidden')
            selected_mcu = request.POST.get('mcu')
            
            # Debug: Print the selected values
            print(f"Selected MCU: {selected_mcu}")
            print(f"Selected board: {selected_board}")
            print(f"Board from visible field: {request.POST.get('board')}")
            print(f"Board from hidden field: {request.POST.get('board_hidden')}")
            print(f"Available boards: {[board['fqbn'] for board in context['boards']]}")
            print(f"Boards for selected MCU: {[board['fqbn'] for board in context['boards'] if board['mcu'] == selected_mcu]}")
            
            for board in context['boards']:
                if board['fqbn'] == selected_board:
                    board_fqbn = board['fqbn']
                    break
            
            if not board_fqbn:
                return render(request, 'upload/esp_upload.html', {
                    'error': f'Please select a valid board for compilation. Selected: {selected_board}, MCU: {selected_mcu}'
                })

            compile_cmd = [
                'arduino-cli', 'compile',
                '-b', board_fqbn,
                '-e',
                '--output-dir', work_dir,
                sketch_dir
            ]

        elif request.POST.get('firmware_type') == 'preset':
            preset_id = request.POST.get('preset_id')
            if not preset_id:
                return render(request, 'upload/esp_upload.html', {
                    'error': 'Please select a preset for preset firmware.'
                })
            preset = Preset.objects.get(id=preset_id)
            generate_firmware(preset, request.POST.get('midi_transfer_mode'))
            # For preset firmware, we don't need to compile, just return to selection
            return redirect('selection')
        
        else:
            return render(request, 'upload/esp_upload.html', {
                'error': 'Please select a firmware type (preset or custom).'
            })

        # Only try to compile if we have a custom firmware
        try:
            subprocess.run(compile_cmd, check=True, capture_output=True)
            output_files = [f for f in os.listdir(work_dir) if f.endswith('.bin') and not f.endswith('.merged.bin')]
            
            # Map know filenames to addresses
            address_map = {
                'bootloader.bin': '0',
                'partitions.bin': '8000',
                'ino.bin': '10000',
                'ota_data_initial.bin': 'e000',
            }

            # Construct output list
            output_items = []
            for f in output_files:
                flash_address = '10000'  # Default address
                for filename_pattern, address in address_map.items():
                    if f.endswith(filename_pattern):
                        flash_address = address
                        break

                url = os.path.join(settings.MEDIA_URL, uid, f)
                output_items.append({
                    'filename': f,
                    'url': request.build_absolute_uri(url),
                    'file_path': os.path.join(uid, f),  # Add file path for JavaScript
                    'address': flash_address,
                })

            context = {'output_items': output_items}
            return render(request, 'upload/esp_upload.html', context)

        except subprocess.CalledProcessError as e:
            return render(request, 'upload/error.html', {
                'error': f"Compilation failed: {e.stderr.decode('utf-8')}"
            })

    return render(request, 'upload/esp_upload.html')

def adafruit_esp_upload(request):
    return render(request, 'upload/adafruit_esp.html')










import shutil

def generate_firmware(preset, modes_string):
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
    # button_count = len(preset.buttons.all())
    joystick = preset.joystick.all()[0] if preset.joystick.all() else None

    if 'usb (otg)' in modes_string:
        firmware_string += '''
#if ARDUINO_USB_MODE
#warning This sketch should be used when USB is in OTG mode

void setup() {}
void loop() {}

#else

'''
        for mode in modes_string.split('+'):
            firmware_string += libs[mode]

    else:
        for mode in modes_string.split('+'):
            firmware_string += libs[mode]

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