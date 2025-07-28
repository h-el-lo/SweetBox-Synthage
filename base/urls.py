from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('sign-up/', views.signUp, name="signup"),
    path('create_preset/', views.create_preset, name='create_preset'),
    path('delete_preset/<str:pk>/', views.delete_preset, name='delete_preset'),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('profile/', views.profile, name="profile"),
    path('about/', views.about, name='about'),
    path('monitor/', views.monitor, name='monitor'),
    path('change_password/', views.change_password, name="change_password"),
    path('toggle_is_private/', views.toggle_is_private, name='toggle_is_private'),
    path('user_presets_json/', views.user_presets_json, name='user_presets_json'),
]
