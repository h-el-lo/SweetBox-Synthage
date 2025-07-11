# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

# Core Django utilities
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from .forms import UserForm, KnobFormSet, ButtonFormSet, JoystickForm, JoystickFormSet
from .models import Preset, Knob, Button
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profile
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import KeypressChannelForm
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
        )
        for i in range(preset.number_of_knobs):
            knob = Knob.objects.create(
                preset=preset,
                CC=i,
                pin=i,
            )

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
        knob_formset = KnobFormSet(request.POST, instance=preset)
        button_formset = ButtonFormSet(request.POST, instance=preset)
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

            # --- Joystick Save Logic ---
            from .models import Joystick
            joystick_instance = getattr(preset, 'joystick', None)
            if preset.has_joystick:
                joystick_form = JoystickForm(request.POST, instance=joystick_instance)
                if joystick_form.is_valid():
                    joystick = joystick_form.save(commit=False)
                    joystick.preset = preset
                    joystick.save()
                else:
                    messages.error(request, 'Please correct the errors in the Joystick form.')
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
                        ),
                        'num_knobs_db': knobs.count() if preset else 0,
                        'num_buttons_db': buttons.count() if preset else 0,
                    }
                    return render(request, 'midi/portal.html', context)
            else:
                # If joystick is disabled, delete any existing joystick for this preset
                if joystick_instance:
                    joystick_instance.delete()

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
                ),
                'num_knobs_db': knobs.count() if preset else 0,
                'num_buttons_db': buttons.count() if preset else 0,
            }
            return render(request, 'midi/portal.html', context)
    else:
        default_knob_initial = {'channel': 1, 'CC': 0, 'min': 0, 'max': 127, 'pin': 0}
        default_button_initial = {'channel': 1, 'mode': 'note', 'noteCC': 0, 'velocityMin': 100, 'max': 127, 'pin': 0}
        knob_formset = KnobFormSet(instance=preset, initial=[default_knob_initial])
        button_formset = ButtonFormSet(instance=preset, initial=[default_button_initial])
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
        'num_knobs_db': knobs.count() if preset else 0,
        'num_buttons_db': buttons.count() if preset else 0,
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
        if form.is_valid():
            user = form.save()
            # Create a default preset for new user
            create_default_preset(user)
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
    }   
    return render(request, 'midi/dashboard.html', context)

@login_required(login_url='login')
def upload(request):
    context = {
        'presets': Preset.objects.filter(owner=request.user),
        'hide_upload_link':True,
    }
    return render(request, 'midi/upload.html', context)

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
        profile.save()
        messages.success(request, 'Profile updated successfully!')
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'midi/profile.html', context)

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
    return render(request, 'midi/change_password.html', {'form': form})

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