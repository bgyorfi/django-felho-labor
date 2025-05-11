# photos/views.py
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib.auth.forms import UserCreationForm 
from django.core.exceptions import PermissionDenied 
from .models import Photo
from .forms import PhotoForm

import requests
import base64
import os
import logging # Új import

logger = logging.getLogger(__name__) # Logger példányosítása

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class PhotoListView(generic.ListView): 
    """Displays the list of uploaded photos."""
    model = Photo
    template_name = 'photos/photo_list.html'
    context_object_name = 'photos'
    paginate_by = 10 

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get('sort', '-upload_date')
        allowed_sort_fields = ['name', '-name', 'upload_date', '-upload_date']
        if sort_by in allowed_sort_fields:
             queryset = queryset.order_by(sort_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-upload_date')
        return context

class PhotoDetailView(generic.DetailView):
    """Displays a single photo."""
    model = Photo
    template_name = 'photos/photo_detail.html'
    context_object_name = 'photo'

class PhotoCreateView(LoginRequiredMixin, generic.CreateView): 
    """Handles photo uploads, requires login."""
    model = Photo
    form_class = PhotoForm
    template_name = 'photos/photo_form.html'
    success_url = reverse_lazy('photo_list')

    def form_valid(self, form):
        logger.debug(f"PhotoCreateView.form_valid called. User: {self.request.user}")
        form.instance.owner = self.request.user
        uploaded_file = form.cleaned_data.get('image')
        filename_for_logging = "unknown_file"

        if uploaded_file:
            filename_for_logging = uploaded_file.name
            logger.debug(f"Uploaded file found: {filename_for_logging}, size: {uploaded_file.size}")
        else:
            logger.warning("No file found in form.cleaned_data['image']")
            form.add_error('image', "Nincs fájl kiválasztva a feltöltéshez.")
            return self.form_invalid(form)
        
        try:
            logger.debug("Reading file content for base64 encoding.")
            encoded_file_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
            logger.debug(f"File base64 encoded. Encoded length: {len(encoded_file_data)}")
            
            api_url = getattr(settings, 'API_GATEWAY_UPLOAD_URL', None)
            if not api_url:
                logger.error("API Gateway URL (API_GATEWAY_UPLOAD_URL) not configured in settings.py.")
                form.add_error(None, "Rendszerkonfigurációs hiba.")
                return self.form_invalid(form)

            headers = {
                'Content-Type': 'application/octet-stream',
                'X-File-Name': uploaded_file.name
            }
            
            logger.info(f"Sending file '{filename_for_logging}' to API Gateway for processing: {api_url}")
            response = requests.post(api_url, data=encoded_file_data.encode('utf-8'), headers=headers, timeout=60) # Timeoutot növeltük
            logger.info(f"Received response from API Gateway. Status: {response.status_code}, Response text: {response.text[:500]}...") # Csak az első 500 karaktert logoljuk a válaszból

            if response.status_code == 200:
                processed_key = None
                try:
                    response_data = response.json()
                    logger.debug(f"API Gateway response JSON data: {response_data}")
                    processed_key = response_data.get('s3_key') 
                    if processed_key:
                        form.instance.processed_s3_key = processed_key 
                        logger.info(f"File '{filename_for_logging}' successfully processed by Lambda. Processed S3 key: {processed_key}")
                    else:
                        logger.warning(f"File '{filename_for_logging}' processed, but S3 key not found in Lambda response. Response: {response_data}")
                        form.add_error(None, "A képfeldolgozás válasza nem tartalmazta az S3 kulcsot.")
                        return self.form_invalid(form)
                except ValueError: 
                    logger.error(f"File '{filename_for_logging}' processed, but Lambda response was not valid JSON: {response.text}", exc_info=True)
                    form.add_error(None, "A képfeldolgozás során belső hiba történt (válasz formátum).")
                    return self.form_invalid(form)
                
                logger.debug("Calling super().form_valid(form) to save Photo instance.")
                logger.debug(f"Photo instance before save: owner={form.instance.owner}, name='{form.instance.name}', processed_s3_key='{form.instance.processed_s3_key}'")
                
                db_response = super().form_valid(form)
                
                if self.object and self.object.pk:
                    logger.info(f"Photo object saved successfully. PK: {self.object.pk}, Processed S3 Key in DB: {self.object.processed_s3_key}")
                else:
                    logger.error("Photo object was not saved successfully or PK not available after save.")
                
                return db_response
            else:
                error_details = f"Status: {response.status_code}. Response: {response.text}"
                logger.error(f"Error uploading file '{filename_for_logging}' to API Gateway. {error_details}")
                form.add_error(None, "Hiba történt a kép szerver oldali továbbítása/feldolgozása során.")
                return self.form_invalid(form)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while sending/processing file '{filename_for_logging}' with API Gateway: {api_url}", exc_info=True)
            form.add_error(None, "A fájl továbbítása vagy feldolgozása időtúllépés miatt megszakadt.")
            return self.form_invalid(form)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while sending file '{filename_for_logging}' to API Gateway. Error: {e}", exc_info=True)
            form.add_error(None, "Hálózati hiba történt a fájl továbbítása közben.")
            return self.form_invalid(form)
        except Exception as e:
            logger.exception(f"Unexpected general error during file processing for '{filename_for_logging}' in Django view.")
            form.add_error(None, "Hiba történt a fájl feldolgozása közben.")
            return self.form_invalid(form)

class PhotoDeleteView(LoginRequiredMixin, generic.DeleteView): 
    """Handles photo deletion with confirmation, requires login and ownership."""
    model = Photo
    template_name = 'photos/photo_confirm_delete.html'
    success_url = reverse_lazy('photo_list')
    context_object_name = 'photo'

    def get_queryset(self):
        """Ensure users can only delete their own photos."""
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)
