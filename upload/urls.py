from django.urls import path
from . import views

urlpatterns = [
    path('', views.selection, name='selection'),
    path('esp_upload/', views.esp_upload, name='esp_upload'),
    path('avr_upload/', views.avr_upload, name='avr_upload'),
    path('adafruit_esp_upload/', views.adafruit_esp_upload, name='adafruit_esp_upload'),
    path('pico_upload/', views.pico_upload, name='pico_upload'),
    path('stm_upload/', views.stm_upload, name='stm_upload'),
    path('arduino/', views.arduino_cli_check, name='arduino'),
    path('input/', views.upload_sketch, name="input"),
    # path('upload2/', views.compile_sketch, name='upload2'),
    # path('output/', views.compile_sketch, name='output'),
    # path('download_firmware/<int:preset_id>/', views.download_firmware, name='download_firmware'),
]
