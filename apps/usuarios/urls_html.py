"""
=============================================================================
URLS AUTENTICACIÓN HTML - ACADEMIA FELINA FLOPPA
=============================================================================
Vistas HTML (Templates con Liquid Glass) para login/registro.
=============================================================================
"""
from django.urls import path
from apps.usuarios.views import LoginTemplateView, RegistroTemplateView

urlpatterns = [
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('registro/', RegistroTemplateView.as_view(), name='registro'),
]