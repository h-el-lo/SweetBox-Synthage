# Generated by Django 4.2.18 on 2025-07-10 11:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keys_channel', models.PositiveSmallIntegerField(default=1)),
                ('number_of_knobs', models.PositiveSmallIntegerField(default=4)),
                ('number_of_buttons', models.PositiveSmallIntegerField(default=0)),
                ('has_joystick', models.BooleanField(default=False)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Preset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('keys_channel', models.PositiveSmallIntegerField(default=1)),
                ('number_of_knobs', models.PositiveSmallIntegerField(default=4)),
                ('number_of_buttons', models.PositiveSmallIntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('has_joystick', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Knob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.PositiveSmallIntegerField(default=1, null=True)),
                ('CC', models.PositiveSmallIntegerField(default=24)),
                ('min', models.IntegerField(default=0)),
                ('max', models.IntegerField(default=127)),
                ('pin', models.IntegerField(default=0)),
                ('preset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='midi.preset')),
            ],
        ),
        migrations.CreateModel(
            name='Joystick',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x_channel', models.PositiveSmallIntegerField(default=1)),
                ('x_pin', models.IntegerField(default=0)),
                ('x_mode', models.CharField(choices=[('pitch', 'Pitch Bend'), ('cc', 'Control Change')], default='pitch', max_length=5)),
                ('x_cc', models.PositiveSmallIntegerField(blank=True, help_text='CC number for X-axis (only used in CC mode)', null=True)),
                ('y_channel', models.PositiveSmallIntegerField(default=1)),
                ('y_pin', models.IntegerField(default=1)),
                ('y_cc', models.PositiveSmallIntegerField(default=2, help_text='CC number for Y-axis')),
                ('preset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='midi.preset')),
            ],
        ),
        migrations.CreateModel(
            name='Button',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.PositiveSmallIntegerField(default=1, null=True)),
                ('mode', models.CharField(choices=[('note', 'Note'), ('cc', 'Control Change')], default='note', max_length=4)),
                ('noteCC', models.PositiveSmallIntegerField(default=0, help_text='Note number or CC number depending on mode')),
                ('velocityMin', models.IntegerField(default=100, help_text='Velocity for notes or minimum CC value')),
                ('max', models.IntegerField(default=127, help_text='Maximum CC value (only used in CC mode)')),
                ('pin', models.IntegerField(default=0)),
                ('preset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='midi.preset')),
            ],
        ),
    ]
