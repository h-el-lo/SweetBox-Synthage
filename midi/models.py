from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Preset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    keys_channel = models.PositiveSmallIntegerField(default=1)
    number_of_knobs = models.PositiveSmallIntegerField(default=4)
    number_of_buttons = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    has_joystick = models.BooleanField(default=False)

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
    # knob_index =
    # pin = 

    objects = models.Manager()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)


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
        return f"{self.mode.title()} Button on Pin {self.pin}"


class Joystick(models.Model):
    MODE_CHOICES = [
        ('pitch', 'Pitch Bend'),
        ('cc', 'Control Change'),
    ]

    preset = models.ForeignKey(Preset, on_delete=models.CASCADE, null=True)

    # X-axis configuration
    x_mode = models.CharField(max_length=5, choices=MODE_CHOICES, default='pitch')
    x_channel = models.PositiveSmallIntegerField(default=1)
    x_cc = models.PositiveSmallIntegerField(null=True, blank=True, help_text='CC number for X-axis (only used in CC mode)')
    x_pin = models.IntegerField(default=0)

    # Y-axis configuration
    y_channel = models.PositiveSmallIntegerField(default=1)
    y_cc = models.PositiveSmallIntegerField(default=2, help_text='CC number for Y-axis')
    y_pin = models.IntegerField(default=1)

    objects = models.Manager()

    def __str__(self):
        return f"Joystick ({self.x_mode} X, CC Y) on Pins {self.x_pin},{self.y_pin}"