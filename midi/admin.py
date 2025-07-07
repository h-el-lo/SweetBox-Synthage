from django.contrib import admin
from .models import Preset, Knob, Joystick, ModWheel, PitchWheel, Button

# Register your models here.
admin.site.register(Preset)
admin.site.register(Knob)
admin.site.register(Button)
admin.site.register(Joystick)
admin.site.register(ModWheel)
admin.site.register(PitchWheel)