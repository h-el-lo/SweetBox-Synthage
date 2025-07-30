from django.urls import path
from . import views

urlpatterns = [
    path('create_preset/', views.create_preset, name='create_preset'),
    path('', views.selection, name='selection'),
    path('upload/', views.upload, name='upload'),
    path('arduino/', views.arduino_cli_check, name='arduino'),
    path('download_firmware/<int:preset_id>/', views.download_firmware, name='download_firmware'),
]
