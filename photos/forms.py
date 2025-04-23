# photos/forms.py
from django import forms
from .models import Photo

class PhotoForm(forms.ModelForm):
    """Form for uploading photos."""
    class Meta:
        model = Photo
        fields = ['name', 'image']