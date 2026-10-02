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
    # ------------------------------------------------------------------
    # RUTAS LEGACY (se mantienen montadas en /api/carro/ vía urls_carro.py)
    # ------------------------------------------------------------------
    path('carro/', include(carro_router.urls)),
    path('carro/agregar/', CarroMatriculaViewSet.as_view({'post': 'agregar'}), name='carro-agregar'),
    path('carro/quitar/<int:curso_id>/', CarroMatriculaViewSet.as_view({'delete': 'quitar'}), name='carro-quitar'),
    path('carro/limpiar/', CarroMatriculaViewSet.as_view({'delete': 'limpiar'}), name='carro-limpiar'),
    path('carro/checkout/', CarroMatriculaViewSet.as_view({'post': 'checkout'}), name='carro-checkout'),

    # Mis órdenes endpoints: /api/matriculas/
    path('', include(ordenes_estudiante_router.urls)),

    # Gestión coordinador endpoints: /api/matriculas/
    path('', include(ordenes_coordinador_router.urls)),

    # ==================================================================
    # ALIASES EXACTOS DE LA MATRIZ DE PERMISOS DE LA PAUTA (Proyecto 2)
    # ------------------------------------------------------------------
    # La pauta EVA 2 lista textualmente estas rutas:
    #   ESTUDIANTE : POST /api/matriculas/confirmar/
    #                GET  /api/mis-matriculas/
    #   COORDINADOR: PATCH /api/matriculas/{id}/estado/
    #
    # Internamente NO son implementaciones distintas: reutilizan la MISMA
    # vista/acción que ya existe (checkout, list, cambiar_estado). Así el
    # código no se duplica y el endpoint responde exactamente igual.
    # Se documentan en Swagger para que la rúbrica quede explícita.
    # ==================================================================

    # POST /api/matriculas/confirmar/  == POST /api/carro/checkout/
    # Liquida el carro y crea la Orden en estado PENDIENTE.
    path(
        'confirmar/',
        CarroMatriculaViewSet.as_view({'post': 'checkout'}),
        name='matriculas-confirmar',
    ),

    # GET /api/mis-matriculas/  (alias exacto de la pauta; vive en
    # academia_felina/urls.py porque el prefijo correcto es /api/, no
    # /api/matriculas/. Ver ahí el bloque "ALIASES DE LA PAUTA").

    # PATCH /api/matriculas/{id}/estado/  == PATCH /api/matriculas/gestion/{id}/estado/
    # Sólo COORDINADOR: PENDIENTE|PAGADO -> ENTREGADO o CANCELADO.
    path(
        '<int:pk>/estado/',
        OrdenMatriculaCoordinadorViewSet.as_view({'patch': 'cambiar_estado'}),
        name='matriculas-estado',
    ),
]