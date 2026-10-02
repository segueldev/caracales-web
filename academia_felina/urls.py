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

urlpatterns = [
    # Health check
    path('health/', include('apps.core.urls')),

    # Django Admin
    path('admin/', admin.site.urls),

    # API Schema (OpenAPI 3.0) - Swagger/Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Endpoints
    path('api/auth/', include('apps.usuarios.urls')),
    path('api/catalogo/', include('apps.academico.urls')),
    path('api/carro/', include('apps.matriculas.urls')),
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