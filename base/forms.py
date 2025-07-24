from django import forms
from django.forms import ModelForm, BaseModelFormSet, ValidationError, modelformset_factory, inlineformset_factory
from django.contrib.auth.models import User


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'password', 
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user