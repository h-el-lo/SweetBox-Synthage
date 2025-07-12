from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('preset/', views.portal, name="portal"),
    path('sign-up/', views.signUp, name="signup"),
    path('create_preset/', views.create_preset, name='create_preset'),
    path('delete_preset/<str:pk>/', views.delete_preset, name='delete_preset'),
    path('upload/', views.upload, name='upload'),
    path('download_firmware/<int:preset_id>/', views.download_firmware, name='download_firmware'),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('profile/', views.profile, name="profile"),
    path('about/', views.about, name='about'),
    path('change_password/', views.change_password, name="change_password"),
    path('toggle_is_private/', views.toggle_is_private, name='toggle_is_private'),
]
