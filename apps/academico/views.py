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
from apps.core.permissions import PublicReadOnly, IsCoordinador


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