"""
=============================================================================
URLS PRINCIPALES - ACADEMIA FELINA FLOPPA
=============================================================================
Configuración de rutas API, Admin, Swagger, Auth y vistas base.
=============================================================================
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from apps.matriculas.views import OrdenMatriculaViewSet

urlpatterns = [
    # ==================================================================
    # ALIASES EXACTOS DE LA MATRIZ DE PERMISOS DE LA PAUTA (Proyecto 2)
    # ------------------------------------------------------------------
    # La pauta EVA 2 enumera textualmente para el ESTUDIANTE:
    #     GET /api/mis-matriculas/
    # Esta vista es la MISMA que atiende /api/matriculas/mis-ordenes/ y
    # /api/matriculas/mis-matriculas/: un único ViewSet, varias rutas.
    # `get_queryset()` filtra por `estudiante=self.request.user`, así que
    # sólo devuelve las órdenes del usuario del token.
    # ==================================================================
    path(
        'api/mis-matriculas/',
        OrdenMatriculaViewSet.as_view({'get': 'list'}),
        name='api-mis-matriculas',
    ),
    path(
        'api/mis-matriculas/<int:pk>/',
        OrdenMatriculaViewSet.as_view({'get': 'retrieve'}),
        name='api-mis-matriculas-detalle',
    ),
    path(
        'api/mis-matriculas/<int:pk>/pagar/',
        OrdenMatriculaViewSet.as_view({'post': 'pagar'}),
        name='api-mis-matriculas-pagar',
    ),
    path(
        'api/mis-matriculas/<int:pk>/cancelar/',
        OrdenMatriculaViewSet.as_view({'post': 'cancelar'}),
        name='api-mis-matriculas-cancelar',
    ),

    # Django Admin
    # NOTA: no se hace `include('apps.core.urls')` con prefijo 'health/' porque
    # eso montaba las VISTAS HTML de core bajo /health/ (duplicando todo el
    # sitio) y hacía que /health/ devolviera la home en vez del JSON del
    # health check. La ruta 'health/' ya está definida dentro de core/urls.py.
    path('admin/', admin.site.urls),

    # API Schema (OpenAPI 3.0) - Swagger/Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Endpoints
    path('api/auth/', include('apps.usuarios.urls')),
    path('api/catalogo/', include('apps.academico.urls')),
    # Carro (rutas "peladas": /api/carro/agregar/ , /api/carro/checkout/ , ...).
    # apps.matriculas/urls.py no sirve aquí porque ahí las rutas del carro
    # llevan un prefijo "carro/" extra y se duplicaría el segmento (daba 404).
    path('api/carro/', include('apps.matriculas.urls_carro')),
    path('api/matriculas/', include('apps.matriculas.urls')),

    # Vistas HTML base (Templates con Liquid Glass) - Footer con datos alumno
    path('', include('apps.core.urls')),

    # Auth HTML Views (Login, Registro)
    path('', include('apps.usuarios.urls_html')),

    # Logout HTML (usa vista de Django)
    path('logout/', DjangoLogoutView.as_view(next_page='home'), name='logout'),
]

# Archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # En desarrollo, servir estáticos desde STATICFILES_DIRS (no STATIC_ROOT que está vacío)
    from django.contrib.staticfiles.views import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'insecure': True}),
    ]