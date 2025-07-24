from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    keys_channel = models.PositiveSmallIntegerField(default=1)
    number_of_knobs = models.PositiveSmallIntegerField(default=4)
    number_of_buttons = models.PositiveSmallIntegerField(default=0)
    has_joystick = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False, help_text='Default privacy setting for new presets')

    objects = models.Manager()

    def __str__(self):
        return f"Profile for {self.owner}"
