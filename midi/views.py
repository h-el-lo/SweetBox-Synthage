# class preset
# contains  mod x, y settings 
# generate firmware of class "preset", flash firmware to either atmega 32u4, rp2040 or esp32 s3

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm
from .forms import KnobFormSet
from .models import Preset, Knob
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import os
from django.http import FileResponse
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
    else:
        knobs = Knob.objects.none()
    firmware_path = None

    knob_queryset = Knob.objects.filter(preset=preset)

    if request.method == 'POST':
        knob_formset = KnobFormSet(request.POST, queryset=knob_queryset)
        midi_form = KeypressChannelForm(request.POST)
        preset_name_value = request.POST.get('preset_name', preset.name if preset else '')

        if knob_formset.is_valid() and midi_form.is_valid():
            # Persist each knob form explicitly so that every new knob is saved.
            knobs_saved = 0  # Counter for the number of active (non-deleted) knobs

            for form in knob_formset:
                # Skip forms that are marked for deletion
                if form.cleaned_data.get('DELETE', False):
                    # If an existing knob is marked for deletion, remove it from DB
                    if form.instance.pk:
                        form.instance.delete()
                    continue

                # Save new or updated knob instance
                knob = form.save(commit=False)
                # Ensure the knob is linked to the current preset before saving
                knob.preset = preset
                knob.save()
                knobs_saved += 1

            # After processing all forms, knobs_saved reflects the actual knob count
            # (i.e., total forms minus deleted ones).
            preset.number_of_knobs = knobs_saved
            preset.keys_channel = midi_form.cleaned_data['midi_channel']
            new_name = preset_name_value.strip()
            if new_name and new_name != preset.name:
                preset.name = new_name
            preset.save()
            messages.success(request, f'Preset "{preset.name}" saved successfully!')
            return redirect(f"{reverse('portal')}?preset={preset.id}")
        else:
            # On error, preserve entered values and show error messages
            messages.error(request, 'Please correct the errors below.')
            context = {
                'knob_formset': knob_formset,
                'preset': preset,
                'presets': presets,
                'download_url': None,
                'hide_portal_link': True,
                'midi_form': midi_form,
                'preset_name_value': preset_name_value,
                'form_errors': knob_formset.non_form_errors() + (midi_form.errors.get('__all__', []) if midi_form.errors else [])
            }
            return render(request, 'midi/portal.html', context)
    else:
        knob_formset = KnobFormSet(queryset=knob_queryset, initial=[{'channel': 1, 'CC': 0, 'min': 0, 'max': 127, 'pin': 0}])
        midi_form = KeypressChannelForm(initial={'midi_channel': preset.keys_channel if preset else 1})
        preset_name_value = preset.name if preset else ''

    download_url = None
    if firmware_path:
        download_url = f'/download_firmware/{preset.id}/'

    context = {
        'knob_formset': knob_formset,
        'preset': preset,
        'presets': presets,
        'download_url': download_url,
        'hide_portal_link': True,
        'midi_form': midi_form,
    }

    return render(request, 'midi/portal.html', context)


def generate_firmware(request):
    preset = Preset.objects.get(id=1)
    # Improved firmware generation logic
    firmware_template = '''
// SweetBox SYNTHAGE Firmware
// Preset: {preset_name}
const int NUM_KNOBS = {num_knobs};
int knobChannels[NUM_KNOBS] = {{ {channels} }};
int knobCCs[NUM_KNOBS] = {{ {ccs} }};
int knobMins[NUM_KNOBS] = {{ {mins} }};
int knobMaxs[NUM_KNOBS] = {{ {maxs} }};
// ... rest of your firmware ...
'''
    knob_objs = Knob.objects.filter(preset=preset)
    firmware_content = firmware_template.format(
        preset_name=preset.name,
        num_knobs=knob_objs.count(),
        channels=', '.join(str(k.channel) for k in knob_objs),
        ccs=', '.join(str(k.CC) for k in knob_objs),
        mins=', '.join(str(k.min) for k in knob_objs),
        maxs=', '.join(str(k.max) for k in knob_objs),
    )
    firmware_dir = os.path.join(settings.BASE_DIR, 'generated_firmware')
    os.makedirs(firmware_dir, exist_ok=True)
    firmware_path = os.path.join(firmware_dir, f'firmware_preset_{preset.id}.ino')
    with open(firmware_path, 'w') as f:
        f.write(firmware_content)
    messages.success(request, 'Settings saved and firmware generated!')
    return redirect(f"{reverse('portal')}?preset={preset.id}")
    pass


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
        user = request.user

        preset = Preset.objects.create(
            owner=user,
            name=name,
            keys_channel=keys_channel,
            number_of_knobs=number_of_knobs,
        )
        # Create the corresponding number of knob objects as stated in the preset
        for i in range(preset.number_of_knobs):
            knob = Knob.objects.create(
                preset=preset,
                channel=1,
                CC=i,
                min=0,
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
    presets = Preset.objects.filter(owner=user)
    preset_count = presets.count()

    context = {
        'hide_dashboard_link':True,
        'presets':presets,
        'preset_count':preset_count,
    }   
    return render(request, 'midi/dashboard.html', context)
