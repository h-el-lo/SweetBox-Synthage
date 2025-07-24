from django.urls import path, include
from .import views

urlpatterns = [
    path('', views.portal, name='portal'),
]