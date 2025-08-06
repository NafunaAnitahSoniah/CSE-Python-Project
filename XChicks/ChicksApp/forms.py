from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ValidationError
from django.forms import ModelForm

#this usercreation form inherits some attributes from the default django UserCreationForm
class UserCreation(UserCreationForm):
    class Meta:
        #instruct this form to take on the fields from the UserProfile model
        model = UserProfile
        fields = "__all__"
    def save(self, commit = True):
        user = super(UserCreation,self).save(commit = False)
        if commit:
            user.is_active = True
            user.is_staff = True
            user.save()
        return user
    







