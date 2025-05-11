# photos/forms.py
from django import forms
from .models import Photo

class PhotoForm(forms.ModelForm):
    """Form for uploading photos."""
    processed_s3_key = forms.CharField(widget=forms.HiddenInput(), required=False) 
    
    class Meta:
        model = Photo
        fields = ['name', 'image', 'processed_s3_key']