# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

# Core Django utilities
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from presets.models import Preset, Knob, Button
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from base.models import Profile
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

def get_preset_defaults(user):
    """Get default values for new presets based on user profile or model defaults"""
    if user.is_authenticated:
        try:
            profile = Profile.objects.get(owner=user)
            return {
                'keys_channel': profile.keys_channel,
                'number_of_knobs': profile.number_of_knobs,
                'number_of_buttons': profile.number_of_buttons,
                'has_joystick': profile.has_joystick,
                'is_private': profile.is_private,
            }
        except Profile.DoesNotExist:
            pass
    
    # Return model defaults if no user or no profile
    return {
        'keys_channel': 1,
        'number_of_knobs': 4,
        'number_of_buttons': 0,
        'has_joystick': False,
        'is_private': False,
    }

    user = request.user
    search_query = request.GET.get('search', '').strip()
    presets = None
    if search_query:
        from django.db.models import Q
        presets = Preset.objects.filter(
            (
                Q(name__icontains=search_query) |
                Q(owner__username__icontains=search_query)
            ) & (
                Q(is_private=False) |
                Q(owner=user)
            )
        ).select_related('owner')
    if user.is_authenticated:
        create_default_preset(user)
    context = {
        'hide_home_link': True,
        'presets': presets,
        'search_query': search_query,
    }   
    return render(request, 'midi/home.html', context)


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
        has_joystick = 'has_joystick' in request.POST
        is_private = request.POST.get('is_private', 'false') == 'true'
        user = request.user

        preset = Preset.objects.create(
            owner=user,
            name=name,
            keys_channel=keys_channel,
            number_of_knobs=number_of_knobs,
            number_of_buttons=number_of_buttons,
            has_joystick=has_joystick,
            is_private=is_private,
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
def upload(request):
    context = {
        'presets': Preset.objects.filter(owner=request.user),
        'hide_upload_link':True,
    }
    return render(request, 'midi/upload.html', context)
