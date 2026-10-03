"""
=============================================================================
VISTAS ACADÉMICAS - ACADEMIA FELINA FLOPPA
=============================================================================
ViewSets para Áreas y Cursos con permisos RBAC:
- Público: GET list/detail (catálogo)
- Coordinador: CRUD completo (POST/PUT/PATCH/DELETE)
=============================================================================
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.academico.models import AreaConocimiento, Curso
from apps.academico.serializers import (
    AreaListSerializer, AreaDetailSerializer, AreaCoordinadorSerializer,
    CursoListSerializer, CursoDetailSerializer, CursoCoordinadorSerializer
)
from apps.academico.filters import CursoFilter, AreaFilter
from apps.academico.barcodes import es_codigo_valido, svg_codigo_barras
from apps.core.permissions import PublicReadOnly, IsCoordinador
from django.http import Http404, HttpResponse


class AreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Áreas de Conocimiento.
    
    Permisos:
    - GET (list, retrieve): Público (AllowAny)
    - POST/PUT/PATCH/DELETE: Solo COORDINADOR
    
    Filtros: activa, search
    """
    queryset = AreaConocimiento.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AreaFilter
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['orden', 'nombre', 'created_at']
    ordering = ['orden', 'nombre']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return AreaCoordinadorSerializer
        elif self.action == 'retrieve':
            return AreaDetailSerializer
        return AreaListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsCoordinador()]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def cursos(self, request, pk=None):
        """Endpoint anidado: GET /api/catalogo/areas/{id}/cursos/"""
        area = self.get_object()
        cursos = area.cursos.filter(activo=True, is_deleted=False, estado=Curso.Estado.PUBLICADO)
        serializer = CursoListSerializer(cursos, many=True, context={'request': request})
        return Response(serializer.data)


class CursoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Cursos/Bootcamps.
    
    Permisos:
    - GET (list, retrieve): Público (AllowAny) - Catálogo
    - POST/PUT/PATCH/DELETE: Solo COORDINADOR
    
    Filtros (django-filter): 
    - area, area_nombre, modalidad, estado
    - precio_min, precio_max
    - fecha_inicio_desde, fecha_inicio_hasta
    - disponible (bool), destacado, activo
    - search (texto en nombre, desc, código, área)
    
    CUMPLE PAUTA: "django-filter configurado en endpoints de consulta"
    """
    queryset = Curso.objects.filter(is_deleted=False).select_related('area', 'coordinador').prefetch_related('prerequisitos')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CursoFilter
    search_fields = ['nombre', 'resumen', 'descripcion', 'codigo', 'area__nombre']
    ordering_fields = ['fecha_inicio', 'precio', 'nombre', 'created_at', 'cupos_disponibles']
    ordering = ['-fecha_inicio']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return CursoCoordinadorSerializer
        elif self.action == 'retrieve':
            return CursoDetailSerializer
        return CursoListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsCoordinador()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Para listado público, solo mostrar PUBLICADO y activos
        if self.action == 'list' and not self.request.user.is_authenticated:
            return qs.filter(activo=True, estado=Curso.Estado.PUBLICADO)
        if self.action == 'list' and self.request.user.is_authenticated:
            if self.request.user.es_coordinador:
                return qs  # Coordinador ve todos
            return qs.filter(activo=True, estado=Curso.Estado.PUBLICADO)
        return qs

    def perform_create(self, serializer):
        # Asignar coordinador automáticamente
        serializer.save(coordinador=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def disponibilidad(self, request, pk=None):
        """Verifica disponibilidad en tiempo real para un curso"""
        curso = self.get_object()
        return Response({
            'curso_id': curso.id,
            'codigo': curso.codigo,
            'nombre': curso.nombre,
            'cupos_maximos': curso.cupos_maximos,
            'cupos_disponibles': curso.cupos_disponibles,
            'cupos_ocupados': curso.cupos_ocupados,
            'esta_disponible': curso.esta_disponible,
            'fecha_limite_inscripcion': curso.fecha_limite_inscripcion,
        })


# ---------------------------------------------------------------------------
# IMAGEN DE CÓDIGO DE BARRAS
# ---------------------------------------------------------------------------
# Es una vista de Django "a secas", NO una de DRF, y eso es deliberado:
#
#   * Devuelve image/svg+xml, no JSON: si se escribiera con @api_view, DRF la
#     envolvería en el renderizador de la petición y habría que pelear con los
#     formatos para que no devuelva texto entre medio.
#   * Al no ser APIView, drf-spectacular NO la incluye en /api/docs/. El
#     Swagger documenta recursos con contrato (JSON); meter ahí una imagen
#     binaria sólo añade ruido a la documentación que revisa el profesor.
#
# Pública y cacheada: la información que transporta (el código del curso) ya
# está a la vista en la propia tabla del catálogo, y se cachéa para que cada
# redibujado del DataTable no tenga que regenerar el SVG.
# ---------------------------------------------------------------------------
def codigo_barras(request, codigo):
    """
    ``GET /api/catalogo/codigos/<codigo>.svg``

    Devuelve el código de barras Code 39 del código de curso.

    Respuestas:
        200 -> image/svg+xml (SVG puro)
        404 -> si el código está vacío, trae símbolos que Code 39 no conoce
               (``Ñ``, acentos, emoji…) o no corresponde a ningún curso. Se
               responde 404 y no 500: un código inexistente es un recurso que
               no está, no un fallo del servidor.
    """
    codigo = (codigo or '').strip().upper()

    if not es_codigo_valido(codigo):
        raise Http404(f'{codigo!r} no es un código codificable como Code 39')

    # Existe el curso: sin esto, cualquiera podría pedir imágenes arbitrarias
    # escribiendo cualquier cadena válida en la URL, y además el 404 sería más
    # honesto (no es que el formato esté mal, es que ese curso no existe).
    if not Curso.objects.filter(codigo=codigo, is_deleted=False).exists():
        raise Http404(f'No existe un curso con código {codigo!r}')

    respuesta = HttpResponse(
        svg_codigo_barras(codigo),
        content_type='image/svg+xml; charset=utf-8',
    )
    # Los códigos no cambian nunca: 24 h en el navegador evita repetir la
    # generación en cada visita y cada paginado del catálogo.
    respuesta['Cache-Control'] = 'public, max-age=86400'
    return respuesta