"""
=============================================================================
URLS AUTENTICACIÓN API - ACADEMIA FELINA FLOPPA
=============================================================================
Endpoints JWT con claims de rol personalizados.
=============================================================================
"""
from django.urls import path
from apps.usuarios.views import (
    RegistroView, LoginView, CustomTokenRefreshView,
    PerfilView, CambioPasswordView, LogoutView
)

urlpatterns = [
    # API Endpoints JWT
    path('registro/', RegistroView.as_view(), name='auth-registro'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('perfil/', PerfilView.as_view(), name='auth-perfil'),
    path('cambio-password/', CambioPasswordView.as_view(), name='auth-cambio-password'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]