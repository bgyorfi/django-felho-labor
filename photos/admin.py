from django.contrib import admin
from photos.models import Photo

# Register your models here.
@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface options for the Photo model."""
    list_display = ('name', 'upload_date', 'image')
    list_filter = ('upload_date',) 
    search_fields = ('name',) 