"""
=============================================================================
URLS CORE - ACADEMIA FELINA FLOPPA
=============================================================================
Vistas HTML base (templates con liquid glass) y API endpoints core.
=============================================================================
"""
from django.urls import path
from apps.core.views import (
    HomeView, CatalogoView, MiCarroView, MisMatriculasView,
    CoordinadorDashboardView, PerfilView, HealthCheckView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
    path('mi-carro/', MiCarroView.as_view(), name='mi_carro'),
    path('mis-matriculas/', MisMatriculasView.as_view(), name='mis_matriculas'),
    path('coordinador/', CoordinadorDashboardView.as_view(), name='coordinador_dashboard'),
    path('perfil/', PerfilView.as_view(), name='perfil'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]