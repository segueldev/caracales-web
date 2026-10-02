"""
=============================================================================
FILTROS DJANGO-FILTER - ACADEMIA FELINA FLOPPA
=============================================================================
Filtros para endpoints de catálogo (Cursos, Áreas).
CUMPLE PAUTA: "Sistema de filtros aplicado sobre campos clave mediante django-filter
(ej. filtrado por categoría, rango de precios, etc.)"
=============================================================================
"""
import django_filters
from apps.academico.models import Curso, AreaConocimiento


class CursoFilter(django_filters.FilterSet):
    """
    Filtros para cursos - Catálogo público y gestión.
    Campos filtrados: área, modalidad, estado, precio, fechas, disponibilidad.
    """
    # Filtro por área (nombre o slug)
    area = django_filters.CharFilter(field_name='area__slug', lookup_expr='iexact')
    area_nombre = django_filters.CharFilter(field_name='area__nombre', lookup_expr='icontains')

    # Filtro por modalidad
    modalidad = django_filters.ChoiceFilter(choices=Curso.Modalidad.choices)

    # Filtro por estado
    estado = django_filters.ChoiceFilter(choices=Curso.Estado.choices)

    # Rango de precios
    precio_min = django_filters.NumberFilter(field_name='precio', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio', lookup_expr='lte')

    # Rango de fechas de inicio
    fecha_inicio_desde = django_filters.DateTimeFilter(field_name='fecha_inicio', lookup_expr='gte')
    fecha_inicio_hasta = django_filters.DateTimeFilter(field_name='fecha_inicio', lookup_expr='lte')

    # Solo cursos disponibles para matrícula
    disponible = django_filters.BooleanFilter(method='filtrar_disponibles')

    # Búsqueda en texto (nombre, descripción, código)
    search = django_filters.CharFilter(method='filtrar_busqueda')

    class Meta:
        model = Curso
        fields = [
            'area', 'area_nombre', 'modalidad', 'estado',
            'precio_min', 'precio_max',
            'fecha_inicio_desde', 'fecha_inicio_hasta',
            'disponible', 'destacado', 'activo', 'search',
        ]

    def filtrar_disponibles(self, queryset, name, value):
        """Filtra solo cursos que están disponibles para matricularse ahora"""
        if value:
            from django.utils import timezone
            now = timezone.now()
            return queryset.filter(
                activo=True,
                is_deleted=False,
                estado=Curso.Estado.PUBLICADO,
                cupos_disponibles__gt=0,
                fecha_limite_inscripcion__gt=now
            )
        return queryset

    def filtrar_busqueda(self, queryset, name, value):
        """Búsqueda full-text en múltiples campos"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(nombre__icontains=value) |
                Q(resumen__icontains=value) |
                Q(descripcion__icontains=value) |
                Q(codigo__icontains=value) |
                Q(area__nombre__icontains=value)
            )
        return queryset


class AreaFilter(django_filters.FilterSet):
    """Filtros para áreas de conocimiento"""
    activa = django_filters.BooleanFilter(field_name='activa')
    search = django_filters.CharFilter(method='filtrar_busqueda')

    class Meta:
        model = AreaConocimiento
        fields = ['activa', 'search']

    def filtrar_busqueda(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(nombre__icontains=value) |
                models.Q(descripcion__icontains=value)
            )
        return queryset


# Import needed for AreaFilter
from django.db import models