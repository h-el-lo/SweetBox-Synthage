from django.contrib import admin
from .models import Preset, Knob, Button, Joystick, Profile

# Register your models here.
admin.site.register(Preset)
admin.site.register(Knob)
admin.site.register(Button)
admin.site.register(Joystick)
admin.site.register(Profile)