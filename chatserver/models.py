from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django import forms

class TicTacGameSession(models.Model):
    user = models.ForeignKey(User, blank=False, null=False, related_name='player')
    user2 = models.ForeignKey(User, blank=True, null=True, related_name='player2')
    name  = models.CharField(max_length = 255, unique=True)
    #open, playing, over
    state = models.CharField(max_length = 25)

class UserForm(forms.ModelForm):
    class Meta:
        model = User  
        fields = ["username","password", "first_name", "last_name"]

# class UserProfileForm(forms.ModelForm):
#     class Meta:
#         model = UserProfile
#         exclude = ['user']