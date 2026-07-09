from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile

class RegisterUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']

class ProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile

        fields = [
            "college",
            "year",
            "branch",
        ]