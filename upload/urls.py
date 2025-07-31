from django.urls import path
from . import views

urlpatterns = [
    path('create_preset/', views.create_preset, name='create_preset'),
    path('', views.selection, name='selection'),
    path('upload/', views.upload, name='upload'),
    path('arduino/', views.arduino_cli_check, name='arduino'),
    path('input/', views.upload_sketch, name="input"),
    path('upload2/', views.compile_sketch, name='upload2'),
    path('output/', views.compile_sketch, name='output'),
    path('download_firmware/<int:preset_id>/', views.download_firmware, name='download_firmware'),
]
