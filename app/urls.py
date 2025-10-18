from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Admin do Django (alterado para django-admin)
    path('', include('core.urls')),  # Inclui as URLs do app 'core'
    # ... outras rotas
]