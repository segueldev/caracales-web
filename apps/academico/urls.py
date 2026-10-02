"""
=============================================================================
URLS ACADÉMICAS - ACADEMIA FELINA FLOPPA
=============================================================================
Endpoints del catálogo público y gestión coordinador.
=============================================================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.academico.views import AreaViewSet, CursoViewSet

router = DefaultRouter()
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'cursos', CursoViewSet, basename='curso')

urlpatterns = [
    path('', include(router.urls)),
]