# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

# Core Django utilities
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from .forms import UserForm
from .models import Profile
from presets.models import Preset, Knob, Button
from presets.forms import KnobFormSet, ButtonFormSet, JoystickForm, JoystickFormSet, KeypressChannelForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
# Create your views here.

def create_default_preset(user):
    if (Preset.objects.filter(owner=user).count() < 1) or (Preset.objects.filter(name='Default').count() < 1):
        preset = Preset.objects.create(
            owner = user,
            name = 'Default',
            keys_channel = 1,
            number_of_knobs = 4,
            number_of_buttons = 0,
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

def home(request):
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
    return render(request, 'base/home.html', context)


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
    return render(request, 'base/delete.html', context)


def signUp(request):
    form = UserForm
    page = 'signup'
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a default preset for new user
            create_default_preset(user)
            return redirect('login')


    context = {
        'form':form,
        'page':page,
    }
    return render(request, 'base/login_register.html', context)


def login_view(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'page': page,
    }
    return render(request, 'base/login_register.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully!')
    return redirect('home')


@login_required(login_url='login')
def dashboard(request):
    user = request.user
    presets = Preset.objects.filter(owner=user).order_by('-updated')

    # Filtering logic
    search = request.GET.get('search', '').strip()
    knobs = request.GET.get('knobs', '').strip()
    buttons = request.GET.get('buttons', '').strip()
    joystick = request.GET.get('joystick', '').strip()

    if search:
        presets = presets.filter(name__icontains=search)
    if knobs:
        presets = presets.filter(number_of_knobs=int(knobs))
    if buttons:
        presets = presets.filter(number_of_buttons=int(buttons))
    if joystick == '1':
        presets = presets.filter(has_joystick=True)
    elif joystick == '0':
        presets = presets.filter(has_joystick=False)

    preset_count = presets.count()

    context = {
        'hide_dashboard_link':True,
        'presets':presets,
        'preset_count':preset_count,
        'range_1_17': range(1, 17),
        'range_0_33': range(0, 33),
        'preset_defaults': get_preset_defaults(user),
    }   
    return render(request, 'base/dashboard.html', context)

@login_required(login_url='login')
def profile(request):
    user = request.user
    # Get or create the user's profile
    profile, created = Profile.objects.get_or_create(owner=user)
    if request.method == 'POST':
        # Update default preset settings
        profile.keys_channel = int(request.POST.get('keys_channel', 1))
        profile.number_of_knobs = int(request.POST.get('number_of_knobs', 4))
        profile.number_of_buttons = int(request.POST.get('number_of_buttons', 0))
        profile.has_joystick = 'has_joystick' in request.POST
        profile.is_private = request.POST.get('is_private', 'false') == 'true'
        profile.save()
        messages.success(request, 'Profile updated successfully!')
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'base/profile.html', {'form': form})

@require_POST
@login_required(login_url='login')
def toggle_is_private(request):
    preset_id = request.POST.get('preset_id')
    try:
        preset = Preset.objects.get(id=preset_id, owner=request.user)
        preset.is_private = not preset.is_private
        preset.save()
        return JsonResponse({'success': True, 'is_private': preset.is_private})
    except Preset.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Preset not found or not owned by user.'}, status=404)


def about(request):

    context = {

    }

    return render(request, 'base/about.html', context)