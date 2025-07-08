# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

# Core Django utilities
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from .forms import UserForm, KnobFormSet, ButtonFormSet, JoystickForm
from .models import Preset, Knob, Button
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import KeypressChannelForm
from django.urls import reverse
# Create your views here.

def create_default_preset(user):
    if (Preset.objects.filter(owner=user).count() < 1) or (Preset.objects.filter(name='Default').count() < 1):
        preset = Preset.objects.create(
            owner = user,
            name = 'Default',
            keys_channel = 1,
            number_of_knobs = 4,
        )
        for i in range(preset.number_of_knobs):
            knob = Knob.objects.create(
                preset=preset,
                CC=i,
                pin=i,
            )

def home(request):
    user = request.user
    if user.is_authenticated:
        create_default_preset(user)
    context = {
        'hide_home_link': True,
    }   
    return render(request, 'midi/home.html', context)


@login_required(login_url='login')
def portal(request):
    user = request.user
    presets = Preset.objects.filter(owner=user).order_by('-updated')
    preset_id = request.GET.get('preset')
    if preset_id:
        preset = presets.filter(id=preset_id).first()
    else:
        preset = presets.first()
    if preset:
        knobs = preset.knob_set.all()
        buttons = preset.button_set.all()
    else:
        knobs = Knob.objects.none()
        buttons = Button.objects.none()
    firmware_path = None

    knob_queryset = Knob.objects.filter(preset=preset)
    button_queryset = Button.objects.filter(preset=preset)

    if request.method == 'POST':
        knob_formset = KnobFormSet(request.POST, queryset=knob_queryset)
        button_formset = ButtonFormSet(request.POST, queryset=button_queryset)
        midi_form = KeypressChannelForm(request.POST)
        preset_name_value = request.POST.get('preset_name', preset.name if preset else '')
        joystick_instance = getattr(preset, 'joystick', None)
        if joystick_instance:
            joystick_form = JoystickForm(instance=joystick_instance)
        else:
            joystick_form = JoystickForm(initial={
                'x_channel': 1,
                'x_mode': 'pitch',
                'x_cc': 0,
                'x_pin': 0,
                'y_channel': 1,
                'y_cc': 2,
                'y_pin': 1,
            })

        if knob_formset.is_valid() and button_formset.is_valid() and midi_form.is_valid():
            # Persist each knob form
            knobs_saved = 0
            for form in knob_formset:
                if form.cleaned_data.get('DELETE', False):
                    if form.instance.pk:
                        form.instance.delete()
                    continue

                knob = form.save(commit=False)
                knob.preset = preset
                knob.save()
                knobs_saved += 1

            # Persist each button form
            buttons_saved = 0
            for form in button_formset:
                if form.cleaned_data.get('DELETE', False):
                    if form.instance.pk:
                        form.instance.delete()
                    continue

                button = form.save(commit=False)
                button.preset = preset
                button.save()
                buttons_saved += 1

            # Update preset
            preset.number_of_knobs = knobs_saved
            preset.number_of_buttons = buttons_saved
            preset.keys_channel = midi_form.cleaned_data['midi_channel']
            new_name = preset_name_value.strip()
            if new_name and new_name != preset.name:
                preset.name = new_name
            # Handle has_joystick toggle
            preset.has_joystick = 'has_joystick' in request.POST
            preset.save()
            messages.success(request, f'Preset "{preset.name}" saved successfully!')
            return redirect(f"{reverse('portal')}?preset={preset.id}")
        else:
            # On error, preserve entered values and show error messages
            messages.error(request, 'Please correct the errors below.')
            context = {
                'knob_formset': knob_formset,
                'button_formset': button_formset,
                'preset': preset,
                'presets': presets,
                'download_url': None,
                'hide_portal_link': True,
                'midi_form': midi_form,
                'preset_name_value': preset_name_value,
                'joystick_form': joystick_form,
                'form_errors': (
                    knob_formset.non_form_errors() + 
                    button_formset.non_form_errors() + 
                    (midi_form.errors.get('__all__', []) if midi_form.errors else [])
                )
            }
            return render(request, 'midi/portal.html', context)
    else:
        knob_formset = KnobFormSet(queryset=knob_queryset, initial=[{'channel': 1, 'CC': 0, 'min': 0, 'max': 127, 'pin': 0}])
        button_formset = ButtonFormSet(queryset=button_queryset, initial=[{'channel': 1, 'mode': 'note', 'noteCC': 0, 'velocityMin': 100, 'max': 127, 'pin': 0}])
        midi_form = KeypressChannelForm(initial={'midi_channel': preset.keys_channel if preset else 1})
        preset_name_value = preset.name if preset else ''
        joystick_instance = getattr(preset, 'joystick', None)
        if joystick_instance:
            joystick_form = JoystickForm(instance=joystick_instance)
        else:
            joystick_form = JoystickForm(initial={
                'x_channel': 1,
                'x_mode': 'pitch',
                'x_cc': 0,
                'x_pin': 0,
                'y_channel': 1,
                'y_cc': 2,
                'y_pin': 1,
            })

    download_url = None
    if firmware_path:
        download_url = f'/download_firmware/{preset.id}/'

    context = {
        'knob_formset': knob_formset,
        'button_formset': button_formset,
        'preset': preset,
        'presets': presets,
        'download_url': download_url,
        'hide_portal_link': True,
        'midi_form': midi_form,
        'joystick_form': joystick_form,
    }

    return render(request, 'midi/portal.html', context)


def generate_firmware(request):
    preset = Preset.objects.get(id=1)
    # Improved firmware generation logic
    firmware_template = '''
// SweetBox SYNTHAGE Firmware
// Preset: {preset_name}

// Knob Configuration
const int NUM_KNOBS = {num_knobs};
int knobChannels[NUM_KNOBS] = {{ {channels} }};
int knobCCs[NUM_KNOBS] = {{ {ccs} }};
int knobMins[NUM_KNOBS] = {{ {mins} }};
int knobMaxs[NUM_KNOBS] = {{ {maxs} }};
int knobPins[NUM_KNOBS] = {{ {knob_pins} }};

// Button Configuration
const int NUM_BUTTONS = {num_buttons};
int buttonChannels[NUM_BUTTONS] = {{ {button_channels} }};
char* buttonModes[NUM_BUTTONS] = {{ {button_modes} }};  // "note" or "cc"
int buttonNoteCCs[NUM_BUTTONS] = {{ {button_note_ccs} }};  // Note numbers or CC numbers
int buttonVelocityMins[NUM_BUTTONS] = {{ {button_velocity_mins} }};  // Velocity for notes or min CC value
int buttonMaxs[NUM_BUTTONS] = {{ {button_maxs} }};  // Only used for CC mode
int buttonPins[NUM_BUTTONS] = {{ {button_pins} }};

void setup() {{
    // Initialize pins
    for (int i = 0; i < NUM_KNOBS; i++) {{
        pinMode(knobPins[i], INPUT);
    }}
    for (int i = 0; i < NUM_BUTTONS; i++) {{
        pinMode(buttonPins[i], INPUT_PULLUP);
    }}
    
    // Initialize MIDI
    Serial.begin(31250);  // Standard MIDI baud rate
}}

void loop() {{
    // Handle knobs
    for (int i = 0; i < NUM_KNOBS; i++) {{
        int rawValue = analogRead(knobPins[i]);
        int midiValue = map(rawValue, 0, 1023, knobMins[i], knobMaxs[i]);
        sendCC(knobChannels[i], knobCCs[i], midiValue);
    }}
    
    // Handle buttons
    static bool buttonStates[NUM_BUTTONS] = {{0}};  // Track button states
    for (int i = 0; i < NUM_BUTTONS; i++) {{
        bool currentState = !digitalRead(buttonPins[i]);  // Inverted because of INPUT_PULLUP
        
        if (currentState != buttonStates[i]) {{  // State changed
            buttonStates[i] = currentState;
            
            if (strcmp(buttonModes[i], "note") == 0) {{
                if (currentState) {{  // Button pressed
                    sendNoteOn(buttonChannels[i], buttonNoteCCs[i], buttonVelocityMins[i]);
                }} else {{  // Button released
                    sendNoteOff(buttonChannels[i], buttonNoteCCs[i], 0);
                }}
            }} else {{  // CC mode
                sendCC(buttonChannels[i], buttonNoteCCs[i], 
                      currentState ? buttonMaxs[i] : buttonVelocityMins[i]);
            }}
        }}
    }}
    
    delay(10);  // Small delay to prevent overwhelming the MIDI bus
}}

void sendNoteOn(byte channel, byte note, byte velocity) {{
    Serial.write(0x90 | (channel - 1));
    Serial.write(note);
    Serial.write(velocity);
}}

void sendNoteOff(byte channel, byte note, byte velocity) {{
    Serial.write(0x80 | (channel - 1));
    Serial.write(note);
    Serial.write(velocity);
}}

void sendCC(byte channel, byte cc, byte value) {{
    Serial.write(0xB0 | (channel - 1));
    Serial.write(cc);
    Serial.write(value);
}}
'''
    knob_objs = Knob.objects.filter(preset=preset)
    button_objs = Button.objects.filter(preset=preset)
    
    # Format button modes as string literals
    button_modes = [f'"{obj.mode}"' for obj in button_objs]
    
    firmware_content = firmware_template.format(
        preset_name=preset.name,
        # Knob configuration
        num_knobs=knob_objs.count(),
        channels=', '.join(str(k.channel) for k in knob_objs),
        ccs=', '.join(str(k.CC) for k in knob_objs),
        mins=', '.join(str(k.min) for k in knob_objs),
        maxs=', '.join(str(k.max) for k in knob_objs),
        knob_pins=', '.join(str(k.pin) for k in knob_objs),
        # Button configuration
        num_buttons=button_objs.count(),
        button_channels=', '.join(str(b.channel) for b in button_objs),
        button_modes=', '.join(button_modes),
        button_note_ccs=', '.join(str(b.noteCC) for b in button_objs),
        button_velocity_mins=', '.join(str(b.velocityMin) for b in button_objs),
        button_maxs=', '.join(str(b.max) for b in button_objs),
        button_pins=', '.join(str(b.pin) for b in button_objs),
    )
    
    firmware_dir = os.path.join(settings.BASE_DIR, 'generated_firmware')
    os.makedirs(firmware_dir, exist_ok=True)
    firmware_path = os.path.join(firmware_dir, f'firmware_preset_{preset.id}.ino')
    with open(firmware_path, 'w') as f:
        f.write(firmware_content)
    messages.success(request, 'Settings saved and firmware generated!')
    return redirect(f"{reverse('portal')}?preset={preset.id}")


@login_required(login_url='/login/')
def download_firmware(request, preset_id):
    firmware_dir = os.path.join(settings.BASE_DIR, 'generated_firmware')
    firmware_path = os.path.join(firmware_dir, f'firmware_preset_{preset_id}.ino')
    if os.path.exists(firmware_path):
        return FileResponse(open(firmware_path, 'rb'), as_attachment=True, filename=f'firmware_preset_{preset_id}.ino')
    return redirect(reverse('portal'))


@csrf_exempt
@login_required(login_url='/login/')
def create_preset(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        keys_channel = int(request.POST.get('keys_channel', 1))
        number_of_knobs = int(request.POST.get('number_of_knobs', 4))
        number_of_buttons = int(request.POST.get('number_of_buttons', 0))
        user = request.user

        preset = Preset.objects.create(
            owner=user,
            name=name,
            keys_channel=keys_channel,
            number_of_knobs=number_of_knobs,
            number_of_buttons=number_of_buttons,
        )
        # Create the corresponding number of knob objects
        for i in range(preset.number_of_knobs):
            knob = Knob.objects.create(
                preset=preset,
                channel=1,
                CC=i,
                min=0,
                max=127,
                pin=i
            )
        # Create the corresponding number of button objects
        for i in range(preset.number_of_buttons):
            button = Button.objects.create(
                preset=preset,
                channel=1,
                mode='note',
                noteCC=i,
                velocityMin=100,
                max=127,
                pin=i
            )

        messages.success(request, f'Preset "{name}" created successfully!')
        return redirect('dashboard')
    return redirect('dashboard')


@login_required(login_url='login')
def delete_preset(request, pk):
    preset = Preset.objects.get(id=pk)
    obj = preset.name

    if preset.owner != request.user:
        return HttpResponse('You are not allowed to be here!!', content_type='text/plain')

    if request.method == 'POST':
        preset.delete()
        return redirect('dashboard')

    context = {
        'obj':obj,
        'preset':preset,
    }
    return render(request, 'midi/delete.html', context)


def signUp(request):
    form = UserForm
    page = 'signup'
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid:
            form.save()
            # Create a default preset for new user
            create_default_preset(request.user)
            return redirect('login')


    context = {
        'form':form,
        'page':page,
    }
    return render(request, 'midi/login_register.html', context)


def login_view(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'page': page,
    }
    return render(request, 'midi/login_register.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully!')
    return redirect('home')


@login_required(login_url='login')
def dashboard(request):
    user = request.user
    presets = Preset.objects.filter(owner=user).order_by('-updated')
    preset_count = presets.count()

    context = {
        'hide_dashboard_link':True,
        'presets':presets,
        'preset_count':preset_count,
    }   
    return render(request, 'midi/dashboard.html', context)
