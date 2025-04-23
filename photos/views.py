# photos/views.py
from django.urls import reverse_lazy, reverse
from django.views import generic 
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib.auth.forms import UserCreationForm 
from django.core.exceptions import PermissionDenied 
from .models import Photo
from .forms import PhotoForm

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

class PhotoCreateView(LoginRequiredMixin, generic.CreateView): # CreateView volt korábban is
    """Handles photo uploads, requires login."""
    model = Photo
    form_class = PhotoForm
    template_name = 'photos/photo_form.html'
    success_url = reverse_lazy('photo_list')

    def form_valid(self, form):
        """Assign the current user as the owner before saving."""
        form.instance.owner = self.request.user # Owner beállítása
        return super().form_valid(form)

class PhotoDeleteView(LoginRequiredMixin, generic.DeleteView): 
    """Handles photo deletion with confirmation, requires login and ownership."""
    model = Photo
    template_name = 'photos/photo_confirm_delete.html'
    success_url = reverse_lazy('photo_list')
    context_object_name = 'photo'

    def get_queryset(self):
        """Ensure users can only delete their own photos."""
        queryset = super().get_queryset()
        # Csak azokat a fotókat adja vissza, amik a bejelentkezett felhasználóhoz tartoznak
        return queryset.filter(owner=self.request.user)

    # Extra biztonsági ellenőrzés (opcionális, mivel a get_queryset már szűr)
    # def dispatch(self, request, *args, **kwargs):
    #     obj = self.get_object()
    #     if obj.owner != self.request.user:
    #         raise PermissionDenied("You do not have permission to delete this photo.")
    #     return super().dispatch(request, *args, **kwargs)