"""
=============================================================================
URLS ACADÉMICAS - ACADEMIA FELINA FLOPPA
=============================================================================
Endpoints del catálogo público y gestión coordinador.
=============================================================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.academico import views
from apps.academico.views import AreaViewSet, CursoViewSet

router = DefaultRouter()
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'cursos', CursoViewSet, basename='curso')

urlpatterns = [
    path('', include(router.urls)),
    # Imagen del código de barras de un curso (ver apps/academico/barcodes.py).
    # Va después del router para no chocar con las rutas de los ViewSets.
    path(
        'codigos/<str:codigo>.svg',
        views.codigo_barras,
        name='codigo_barras',
    ),
]