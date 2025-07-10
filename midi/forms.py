from django import forms
from django.forms import ModelForm, BaseModelFormSet, ValidationError, modelformset_factory, inlineformset_factory
from django.contrib.auth.models import User

# Local models actually referenced in this file
from .models import Preset, Knob, Button, Joystick


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'password', 
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class KnobForm(ModelForm):
    channel = forms.IntegerField(
        label='Channel', 
        min_value=1, 
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    CC = forms.IntegerField(
        label='CC Number', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    min = forms.IntegerField(
        label='Minimum Value', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    max = forms.IntegerField(
        label='Maximum Value', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    pin = forms.IntegerField(
        label='Pin Number', 
        min_value=0, 
        max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-99'
        })
    )
    
    class Meta:
        model = Knob
        fields = ['channel', 'CC', 'min', 'max', 'pin']
        labels = {
            'channel': 'Channel',
            'CC': 'CC Number',
            'min': 'Minimum Value',
            'max': 'Maximum Value',
            'pin': 'Pin Number',
        }

    def clean_channel(self):
        channel = self.cleaned_data.get('channel')
        if channel is None:
            raise forms.ValidationError('Channel is required.')
        if not (1 <= channel <= 16):
            raise forms.ValidationError('Channel must be between 1 and 16.')
        return channel

    def clean_CC(self):
        cc = self.cleaned_data.get('CC')
        if cc is None:
            raise forms.ValidationError('CC Number is required.')
        if not (0 <= cc <= 127):
            raise forms.ValidationError('CC number must be between 0 and 127.')
        return cc

    def clean_min(self):
        min_value = self.cleaned_data.get('min')
        if min_value is None:
            raise forms.ValidationError('Minimum value is required.')
        if not (0 <= min_value <= 127):
            raise forms.ValidationError('Min value must be between 0 and 127.')
        return min_value

    def clean_max(self):
        max_value = self.cleaned_data.get('max')
        if max_value is None:
            raise forms.ValidationError('Maximum value is required.')
        if not (0 <= max_value <= 127):
            raise forms.ValidationError('Max value must be between 0 and 127.')
        return max_value

    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        if pin is None:
            raise forms.ValidationError('Pin number is required.')
        if not (0 <= pin <= 99):
            raise forms.ValidationError('Pin number must be between 0 and 99.')
        return pin

    def clean(self):
        cleaned_data = super().clean()
        min_value = cleaned_data.get('min')
        max_value = cleaned_data.get('max')
        return cleaned_data


class BaseKnobFormSet(BaseModelFormSet):
    """Custom formset for Knobs.

    Changes from previous behaviour:
    1. Allows duplicates for CC and Pin numbers.
    2. Permits submitting zero knobs (no ValidationError raised).
    3. Hides the automatically-added ORDER field so we can use it for drag-and-drop re-ordering in the UI.
    """

    # Hide the ORDER field generated when can_order=True so it doesn't show in the table
    ordering_widget = forms.HiddenInput

    def clean(self):
        """Ensure each non-deleted form is fully filled out (all required fields present)."""
        super().clean()

        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue

            # Skip rows flagged for deletion
            if form.cleaned_data.get('DELETE', False):
                continue

            # Verify required fields are provided (duplicates now allowed)
            required_fields = ['channel', 'CC', 'min', 'max', 'pin']
            for field in required_fields:
                if form.cleaned_data.get(field) is None:
                    raise ValidationError('All fields are required for each knob.')


KnobFormSet = inlineformset_factory(
    Preset, 
    Knob,
    form=KnobForm,
    extra=1,
    can_delete=True,
    max_num=24
)


class KeypressChannelForm(forms.Form):
    midi_channel = forms.IntegerField(
        label='Keypress Channel', 
        min_value=1, 
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    
    def clean_midi_channel(self):
        channel = self.cleaned_data.get('midi_channel')
        if channel is None:
            raise forms.ValidationError('MIDI channel is required.')
        if not (1 <= channel <= 16):
            raise forms.ValidationError('MIDI channel must be between 1 and 16.')
        return channel


class PresetForm(forms.ModelForm):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter preset name'
        })
    )
    keys_channel = forms.IntegerField(
        min_value=1,
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    number_of_knobs = forms.IntegerField(
        min_value=0,
        max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-24'
        })
    )
    number_of_buttons = forms.IntegerField(
        min_value=0,
        max_value=32,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-32'
        })
    )
    
    class Meta:
        model = Preset
        fields = ['name', 'keys_channel', 'number_of_knobs', 'number_of_buttons']
        labels = {
            'name': 'Preset Name',
            'keys_channel': 'Keys Channel',
            'number_of_knobs': 'Number of Knobs',
            'number_of_buttons': 'Number of Buttons',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise forms.ValidationError('Preset name is required.')
        return name.strip()
    
    def clean_keys_channel(self):
        channel = self.cleaned_data.get('keys_channel')
        if channel is None:
            raise forms.ValidationError('Keys channel is required.')
        if not (1 <= channel <= 16):
            raise forms.ValidationError('Keys channel must be between 1 and 16.')
        return channel
    
    def clean_number_of_knobs(self):
        knobs = self.cleaned_data.get('number_of_knobs')
        if knobs is None:
            raise forms.ValidationError('Number of knobs is required.')
        if not (0 <= knobs <= 24):
            raise forms.ValidationError('Number of knobs must be between 0 and 24.')
        return knobs

    def clean_number_of_buttons(self):
        buttons = self.cleaned_data.get('number_of_buttons')
        if buttons is None:
            raise forms.ValidationError('Number of buttons is required.')
        if not (0 <= buttons <= 32):
            raise forms.ValidationError('Number of buttons must be between 0 and 32.')
        return buttons


class ButtonForm(ModelForm):
    channel = forms.IntegerField(
        label='Channel', 
        min_value=1, 
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    mode = forms.ChoiceField(
        label='Mode',
        choices=Button.MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    noteCC = forms.IntegerField(
        label='Note/CC Number', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    velocityMin = forms.IntegerField(
        label='Velocity/Min CC', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    max = forms.IntegerField(
        label='Max CC Value', 
        min_value=0, 
        max_value=127,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    pin = forms.IntegerField(
        label='Pin Number', 
        min_value=0, 
        max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-99'
        })
    )
    
    class Meta:
        model = Button
        fields = ['channel', 'mode', 'noteCC', 'velocityMin', 'max', 'pin']
        labels = {
            'channel': 'Channel',
            'mode': 'Mode',
            'noteCC': 'Note/CC Number',
            'velocityMin': 'Velocity/Min CC',
            'max': 'Max CC Value',
            'pin': 'Pin Number',
        }

    def clean_channel(self):
        channel = self.cleaned_data.get('channel')
        if channel is None:
            raise forms.ValidationError('Channel is required.')
        if not (1 <= channel <= 16):
            raise forms.ValidationError('Channel must be between 1 and 16.')
        return channel

    def clean_noteCC(self):
        noteCC = self.cleaned_data.get('noteCC')
        if noteCC is None:
            raise forms.ValidationError('Note/CC Number is required.')
        if not (0 <= noteCC <= 127):
            raise forms.ValidationError('Note/CC number must be between 0 and 127.')
        return noteCC

    def clean_velocityMin(self):
        velocityMin = self.cleaned_data.get('velocityMin')
        if velocityMin is None:
            raise forms.ValidationError('Velocity/Min CC value is required.')
        if not (0 <= velocityMin <= 127):
            raise forms.ValidationError('Velocity/Min CC value must be between 0 and 127.')
        return velocityMin

    def clean_max(self):
        max_value = self.cleaned_data.get('max')
        if max_value is None:
            raise forms.ValidationError('Maximum CC value is required.')
        if not (0 <= max_value <= 127):
            raise forms.ValidationError('Maximum CC value must be between 0 and 127.')
        return max_value

    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        if pin is None:
            raise forms.ValidationError('Pin number is required.')
        if not (0 <= pin <= 99):
            raise forms.ValidationError('Pin number must be between 0 and 99.')
        return pin

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        velocityMin = cleaned_data.get('velocityMin')
        max_value = cleaned_data.get('max')

        if mode == 'note' and max_value != 127:
            cleaned_data['max'] = 127  # Force max to 127 for note mode
        
        return cleaned_data


class BaseButtonFormSet(BaseModelFormSet):
    """Custom formset for Buttons.

    Similar to BaseKnobFormSet:
    1. Allows duplicates for Note/CC and Pin numbers.
    2. Permits submitting zero buttons.
    3. Hides the automatically-added ORDER field for drag-and-drop re-ordering.
    """

    ordering_widget = forms.HiddenInput

    def clean(self):
        """Ensure each non-deleted form is fully filled out (all required fields present)."""
        super().clean()

        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue

            # Skip rows flagged for deletion
            if form.cleaned_data.get('DELETE', False):
                continue

            # Verify required fields are provided (duplicates allowed)
            required_fields = ['channel', 'mode', 'noteCC', 'velocityMin', 'max', 'pin']
            for field in required_fields:
                if form.cleaned_data.get(field) is None:
                    raise ValidationError('All fields are required for each button.')


ButtonFormSet = inlineformset_factory(
    Preset,
    Button,
    form=ButtonForm,
    extra=1,
    can_delete=True,
    max_num=16
)


class JoystickForm(ModelForm):
    x_channel = forms.IntegerField(
        label='X Channel', 
        min_value=1, 
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    x_mode = forms.ChoiceField(
        label='X Mode',
        choices=Joystick.MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    x_cc = forms.IntegerField(
        label='X CC Number', 
        min_value=0, 
        max_value=127,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    x_pin = forms.IntegerField(
        label='X Pin Number', 
        min_value=0, 
        max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-99'
        })
    )
    y_channel = forms.IntegerField(
        label='Y Channel', 
        min_value=1, 
        max_value=16,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1-16'
        })
    )
    y_cc = forms.IntegerField(
        label='Y CC Number', 
        min_value=0, 
        max_value=127,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-127'
        })
    )
    y_pin = forms.IntegerField(
        label='Y Pin Number', 
        min_value=0, 
        max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-99'
        })
    )
    
    class Meta:
        model = Joystick
        fields = ['x_mode', 'x_channel', 'x_cc', 'x_pin', 'y_channel', 'y_cc', 'y_pin']
        labels = {
            'x_mode': 'X Mode',
            'x_channel': 'X Channel',
            'x_cc': 'X CC Number',
            'x_pin': 'X Pin Number',
            'y_channel': 'Y Channel',
            'y_cc': 'Y CC Number',
            'y_pin': 'Y Pin Number',
        }

    def clean_x_cc(self):
        x_mode = self.cleaned_data.get('x_mode')
        x_cc = self.cleaned_data.get('x_cc')
        
        if x_mode == 'cc':
            if x_cc is None:
                raise forms.ValidationError('X axis CC number is required when X axis mode is Control Change.')
            if not (0 <= x_cc <= 127):
                raise forms.ValidationError('CC number must be between 0 and 127.')
        return x_cc

    def clean_y_cc(self):
        y_cc = self.cleaned_data.get('y_cc')
        x_mode = self.cleaned_data.get('x_mode')
        if x_mode == 'cc':
            if y_cc is None:
                raise forms.ValidationError('Y axis CC number is required when X axis mode is Control Change.')
            if not (0 <= y_cc <= 127):
                raise forms.ValidationError('CC number must be between 0 and 127.')
        return y_cc

    def clean_x_pin(self):
        x_pin = self.cleaned_data.get('x_pin')
        if x_pin is None:
            raise forms.ValidationError('X axis pin number is required.')
        if not (0 <= x_pin <= 99):
            raise forms.ValidationError('Pin number must be between 0 and 99.')
        return x_pin

    def clean_y_pin(self):
        y_pin = self.cleaned_data.get('y_pin')
        if y_pin is None:
            raise forms.ValidationError('Y axis pin number is required.')
        if not (0 <= y_pin <= 99):
            raise forms.ValidationError('Pin number must be between 0 and 99.')
        return y_pin

    def clean_x_channel(self):
        x_channel = self.cleaned_data.get('x_channel')
        if x_channel is None:
            raise forms.ValidationError('X axis channel is required.')
        if not (1 <= x_channel <= 16):
            raise forms.ValidationError('Channel must be between 1 and 16.')
        return x_channel

    def clean_y_channel(self):
        y_channel = self.cleaned_data.get('y_channel')
        if y_channel is None:
            raise forms.ValidationError('Y axis channel is required.')
        if not (1 <= y_channel <= 16):
            raise forms.ValidationError('Channel must be between 1 and 16.')
        return y_channel


JoystickFormSet = modelformset_factory(
    Joystick,
    form=JoystickForm,
    extra=0,
    can_delete=True
)