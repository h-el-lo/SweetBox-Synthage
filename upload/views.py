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
from .utils import arduino as ard  
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
        elif mcu and mcu.lower() == 'atmega32u4':
            print(f"Routing to avr_upload for MCU: {mcu}")
            return avr_upload(request)
        # elif request.POST.get('mcu').lower() == 'atmega32u4':
        #     return generate_firmware(request)
        # elif request.POST.get('mcu').lower() == 'rp2040':
        #     return generate_firmware(request)
        else:
            print(f"Redirecting to selection for MCU: {mcu}")
            return redirect('selection')
    else:
        return redirect('selection')

def arduino_cli_check(request):
    is_installed, message = ard.check_installed()

    if is_installed:
        return HttpResponse(f'<p style="color: green;">✅ Installed: { message }</p>')
    else:
        return HttpResponse(f'<p style="color: red;">❌ Not Installed: { message }</p>')

def arduino_boards_check(request):
    is_installed, message = ard.installed_boards()
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
                return render(request, 'upload/error.html', {
                    'error': 'Please select a preset for preset firmware.'
                })
            preset = Preset.objects.get(id=preset_id)
            print(preset)
            
            # Generate firmware string
            firmware_string = ard.generate_esp_firmware(preset, request.POST.get('midi_transfer_mode'))
            
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
            
            # Get board context for compilation
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
        
        else:
            return render(request, 'upload/esp_upload.html', {
                'error': 'Please select a firmware type (preset or custom).'
            })

        # Only try to compile if we have a custom firmware/ preset firmware
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

def avr_upload(request):
    if request.method == 'POST':
        # Check if we have a custom firmware file
        if request.POST.get('firmware_type') == 'custom':
            if 'custom_firmware_file' not in request.FILES:
                return render(request, 'upload/avr_upload.html', {
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
                return render(request, 'upload/avr_upload.html', {
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
                return render(request, 'upload/error.html', {
                    'error': 'Please select a preset for preset firmware.'
                })
            preset = Preset.objects.get(id=preset_id)
            print(preset)
            
            # Generate firmware string
            firmware_string = ard.generate_avr_firmware(preset, request.POST.get('midi_transfer_mode'))
            
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
            
            # Get board context for compilation
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
                return render(request, 'upload/avr_upload.html', {
                    'error': f'Please select a valid board for compilation. Selected: {selected_board}, MCU: {selected_mcu}'
                })

            compile_cmd = [
                'arduino-cli', 'compile',
                '-b', board_fqbn,
                '-e',
                '--output-dir', work_dir,
                sketch_dir
            ]
        
        else:
            return render(request, 'upload/esp_upload.html', {
                'error': 'Please select a firmware type (preset or custom).'
            })

        # Only try to compile if we have a custom firmware/ preset firmware
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
            return render(request, 'upload/avr_upload.html', context)

        except subprocess.CalledProcessError as e:
            return render(request, 'upload/error.html', {
                'error': f"Compilation failed: {e.stderr.decode('utf-8')}"
            })

    return render(request, 'upload/esp_upload.html')


def adafruit_esp_upload(request):
    return render(request, 'upload/adafruit_esp.html')
    

import shutil
