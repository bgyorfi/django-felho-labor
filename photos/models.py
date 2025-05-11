from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
class Photo(models.Model):
    """Represents a photo uploaded by a user (in later phases)."""
    owner = models.ForeignKey( # Kapcsolat a User modellel
        User,
        on_delete=models.CASCADE, # Ha a User törlődik, a képei is törlődjenek
        verbose_name="Feltöltő",
        null=True
    )
    name = models.CharField(
        max_length=40,
        verbose_name="Név" 
    )
    image = models.ImageField(
        upload_to='photos/', # A MEDIA_ROOT könyvtáron belül hova kerüljön
        verbose_name="Képfájl"
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Feltöltés dátuma"
    )
    processed_s3_key = models.CharField(max_length=1024, blank=True, null=True) 

    def __str__(self):
        """String representation of the Photo object."""
        return f"{self.name} ({self.upload_date.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-upload_date'] # Alapértelmezett rendezés (legújabb elöl)
        verbose_name = "Photo"        
        verbose_name_plural = "photos" 

   

    @property
    def display_image_url(self):
        print(f"DEBUG (Photo Model PK {self.pk}): Generating display_image_url. Processed S3 Key: '{self.processed_s3_key}'") # Egyszerűbb print most
        bucket_name = "djangophotoalbumbucket"
        region_name = "eu-north-1"
        url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{self.processed_s3_key}"
        print(f"DEBUG (Photo Model PK {self.pk}): Generated URL: {url}")
        return url