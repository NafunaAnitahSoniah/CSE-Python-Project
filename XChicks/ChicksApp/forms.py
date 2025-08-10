from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserCreation(UserCreationForm):
    class Meta:
        model = UserProfile
        # expose only safe fields for manual registration
        fields = ('username', 'email', 'role', 'phone', 'title')

    def save(self, commit=True):
        user = super().save(commit=False)
        # New users not staff by default; adjust logic if needed
        if commit:
            user.save()
        return user
    







