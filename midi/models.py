from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Profile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    keys_channel = models.PositiveSmallIntegerField(default=1)
    number_of_knobs = models.PositiveSmallIntegerField(default=4)
    number_of_buttons = models.PositiveSmallIntegerField(default=0)
    has_joystick = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"Profile for {self.owner}"

class Preset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    keys_channel = models.PositiveSmallIntegerField(default=1)
    number_of_knobs = models.PositiveSmallIntegerField(default=4)
    number_of_buttons = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    has_joystick = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False, help_text='Mark this preset as private')

    objects = models.Manager() 

    def __str__(self):
        return self.name


# Class for knobs and sliders
class Knob(models.Model):
    preset = models.ForeignKey(Preset, on_delete=models.CASCADE, null=True)
    channel = models.PositiveSmallIntegerField(null=True, default=1)
    CC = models.PositiveSmallIntegerField(default=24)
    min = models.IntegerField(default=0)
    max = models.IntegerField(default=127)
    pin = models.IntegerField(default=0)

    objects = models.Manager()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Preset ({self.preset}): knob {self.pin}"


# Class for buttons
class Button(models.Model):
    MODE_CHOICES = [
        ('note', 'Note'),
        ('cc', 'Control Change'),
    ]

    preset = models.ForeignKey(Preset, on_delete=models.CASCADE, null=True)
    channel = models.PositiveSmallIntegerField(null=True, default=1)
    mode = models.CharField(max_length=4, choices=MODE_CHOICES, default='note')
    noteCC = models.PositiveSmallIntegerField(default=0, help_text='Note number or CC number depending on mode')
    velocityMin = models.IntegerField(default=100, help_text='Velocity for notes or minimum CC value')
    max = models.IntegerField(default=127, help_text='Maximum CC value (only used in CC mode)')
    pin = models.IntegerField(default=0)

    objects = models.Manager()

    def __str__(self):
        return f"Preset ({self.preset}): Button {self.pin}"


class Joystick(models.Model):
    MODE_CHOICES = [
        ('pitch', 'Pitch Bend'),
        ('cc', 'Control Change'),
    ]

    preset = models.ForeignKey(Preset, on_delete=models.CASCADE, null=True)

    # X-axis configuration
    x_channel = models.PositiveSmallIntegerField(default=1)
    x_pin = models.IntegerField(default=0)
    x_mode = models.CharField(max_length=5, choices=MODE_CHOICES, default='pitch')
    x_cc = models.PositiveSmallIntegerField(null=True, blank=True, help_text='CC number for X-axis (only used in CC mode)')
    

    # Y-axis configuration
    y_channel = models.PositiveSmallIntegerField(default=1)
    y_pin = models.IntegerField(default=1)
    y_cc = models.PositiveSmallIntegerField(default=2, help_text='CC number for Y-axis')
    

    objects = models.Manager()

    def __str__(self):
        return f"Joystick ({self.x_mode} X, CC Y) on Pins {self.x_pin},{self.y_pin}"
