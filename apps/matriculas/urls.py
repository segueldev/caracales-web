"""
=============================================================================
URLS MATRÍCULAS - ACADEMIA FELINA FLOPPA
=============================================================================
Endpoints separados para Estudiante (carro, mis órdenes) y Coordinador (gestión).
=============================================================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.matriculas.views import (
    CarroMatriculaViewSet, OrdenMatriculaViewSet, OrdenMatriculaCoordinadorViewSet
)

# Router para Carro de matrícula (Estudiante)
carro_router = DefaultRouter()
carro_router.register(r'', CarroMatriculaViewSet, basename='carro')

# Router para Mis Órdenes (Estudiante)
ordenes_estudiante_router = DefaultRouter()
ordenes_estudiante_router.register(r'mis-ordenes', OrdenMatriculaViewSet, basename='mis-ordenes')

# Router para Gestión Órdenes (Coordinador)
ordenes_coordinador_router = DefaultRouter()
ordenes_coordinador_router.register(r'gestion', OrdenMatriculaCoordinadorViewSet, basename='orden-gestion')

urlpatterns = [
    # Carro endpoints: /api/carro/
    path('carro/', include(carro_router.urls)),
    path('carro/agregar/', CarroMatriculaViewSet.as_view({'post': 'agregar'}), name='carro-agregar'),
    path('carro/quitar/<int:curso_id>/', CarroMatriculaViewSet.as_view({'delete': 'quitar'}), name='carro-quitar'),
    path('carro/limpiar/', CarroMatriculaViewSet.as_view({'delete': 'limpiar'}), name='carro-limpiar'),
    path('carro/checkout/', CarroMatriculaViewSet.as_view({'post': 'checkout'}), name='carro-checkout'),
    
    # Mis órdenes endpoints: /api/matriculas/
    path('', include(ordenes_estudiante_router.urls)),
    
    # Gestión coordinador endpoints: /api/matriculas/
    path('', include(ordenes_coordinador_router.urls)),
]