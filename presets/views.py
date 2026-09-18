from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Preset, Knob, Button, Joystick
from base.models import Profile
from .forms import KnobFormSet, ButtonFormSet, JoystickForm, JoystickFormSet, KeypressChannelForm
from django.urls import reverse

# Create your views here.

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

    if request.method == 'POST':
        knob_formset = KnobFormSet(request.POST, instance=preset)
        button_formset = ButtonFormSet(request.POST, instance=preset)
        midi_form = KeypressChannelForm(request.POST)
        preset_name_value = request.POST.get('preset_name', preset.name if preset else '')
        # Get existing joystick instance for this preset
        joystick_instance = None
        if preset and preset.has_joystick:
            joystick_instance = Joystick.objects.filter(preset=preset).first()
        
        # Handle joystick form with POST data
        joystick_enabled = 'has_joystick' in request.POST
        if joystick_enabled:
            joystick_form = JoystickForm(request.POST, instance=joystick_instance)
        else:
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

        # Check if joystick form is valid when joystick is enabled
        joystick_valid = True
        if joystick_enabled:
            joystick_valid = joystick_form.is_valid()

        if knob_formset.is_valid() and button_formset.is_valid() and midi_form.is_valid() and joystick_valid:
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

            # --- Joystick Save Logic ---
            if joystick_enabled:
                joystick = joystick_form.save(commit=False)
                joystick.preset = preset
                joystick.save()
            else:
                # If joystick is disabled, delete any existing joystick for this preset
                if preset and preset.has_joystick:
                    joystick_instance = Joystick.objects.filter(preset=preset).first()
                    if joystick_instance:
                        joystick_instance.delete()

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
                    (midi_form.errors.get('__all__', []) if midi_form.errors else []) +
                    (joystick_form.errors.get('__all__', []) if joystick_form.errors else [])
                ),
                'num_knobs_db': knobs.count() if preset else 0,
                'num_buttons_db': buttons.count() if preset else 0,
            }
            return render(request, 'presets/portal.html', context)
    else:
        default_knob_initial = {'channel': 1, 'CC': 0, 'min': 0, 'max': 127, 'pin': 0}
        default_button_initial = {'channel': 1, 'mode': 'note', 'noteCC': 0, 'velocityMin': 100, 'max': 127, 'pin': 0}
        knob_formset = KnobFormSet(instance=preset, initial=[default_knob_initial])
        button_formset = ButtonFormSet(instance=preset, initial=[default_button_initial])
        midi_form = KeypressChannelForm(initial={'midi_channel': preset.keys_channel if preset else 1})
        preset_name_value = preset.name if preset else ''
        # Get existing joystick instance for this preset
        joystick_instance = None
        if preset and preset.has_joystick:
            joystick_instance = Joystick.objects.filter(preset=preset).first()
        
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

    context = {
        'knob_formset': knob_formset,
        'button_formset': button_formset,
        'preset': preset,
        'presets': presets,
        'hide_portal_link': True,
        'midi_form': midi_form,
        'joystick_form': joystick_form,
        'num_knobs_db': knobs.count() if preset else 0,
        'num_buttons_db': buttons.count() if preset else 0,
        'preset_defaults': get_preset_defaults(user),
    }

    return render(request, 'presets/portal.html', context)
