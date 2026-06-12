
from django import forms
from .models import UserProfile

class ChangeImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']

# Ensure this form is defined if it is needed
class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']
