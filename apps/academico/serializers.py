"""
=============================================================================
SERIALIZERS ACADÉMICOS - ACADEMIA FELINA FLOPPA
=============================================================================
Serializers para Áreas y Cursos con diferentes niveles de detalle:
- ListSerializer: campos mínimos para listados
- DetailSerializer: todos los campos + relaciones
- CoordinadorSerializer: para gestión admin (CRUD completo)
=============================================================================
"""
from rest_framework import serializers
from apps.academico.models import AreaConocimiento, Curso
from apps.usuarios.models import Usuario


class AreaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listado de áreas (catálogo público)"""
    cursos_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AreaConocimiento
        fields = ['id', 'nombre', 'slug', 'descripcion', 'icono', 'orden', 'cursos_count']


class AreaDetailSerializer(AreaListSerializer):
    """Serializer completo para detalle de área"""
    cursos = serializers.SerializerMethodField()

    class Meta(AreaListSerializer.Meta):
        fields = AreaListSerializer.Meta.fields + ['cursos', 'activa', 'created_at', 'updated_at']

    def get_cursos(self, obj):
        cursos = obj.cursos.filter(activo=True, is_deleted=False, estado=Curso.Estado.PUBLICADO)
        return CursoListSerializer(cursos, many=True, context=self.context).data


class AreaCoordinadorSerializer(serializers.ModelSerializer):
    """Serializer para gestión de áreas (coordinador) - CRUD completo"""
    cursos_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AreaConocimiento
        fields = ['id', 'nombre', 'slug', 'descripcion', 'icono', 'orden', 'activa', 'cursos_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'cursos_count']


class CursoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listado de cursos (catálogo público)"""
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    area_icono = serializers.CharField(source='area.icono', read_only=True)
    coordinador_nombre = serializers.CharField(source='coordinador.get_full_name', read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    cupos_ocupados = serializers.IntegerField(read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id', 'codigo', 'nombre', 'slug', 'resumen', 'imagen_url',
            'area_nombre', 'area_icono', 'coordinador_nombre',
            'modalidad', 'fecha_inicio', 'fecha_fin', 'fecha_limite_inscripcion',
            'cupos_maximos', 'cupos_disponibles', 'cupos_ocupados',
            'precio', 'esta_disponible', 'destacado',
        ]

    def get_imagen_url(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
        return None


class CursoDetailSerializer(CursoListSerializer):
    """Serializer completo para detalle de curso"""
    area = AreaListSerializer(read_only=True)
    prerequisitos = CursoListSerializer(many=True, read_only=True)

    class Meta(CursoListSerializer.Meta):
        fields = CursoListSerializer.Meta.fields + [
            'descripcion', 'area', 'prerequisitos', 'estado',
            'created_at', 'updated_at',
        ]


class CursoCoordinadorSerializer(serializers.ModelSerializer):
    """Serializer para gestión de cursos (coordinador) - CRUD completo"""
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    coordinador_nombre = serializers.CharField(source='coordinador.get_full_name', read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    cupos_ocupados = serializers.IntegerField(read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'codigo', 'nombre', 'slug', 'resumen', 'descripcion',
            'area', 'area_nombre', 'coordinador', 'coordinador_nombre',
            'imagen', 'estado', 'modalidad',
            'fecha_inicio', 'fecha_fin', 'fecha_limite_inscripcion',
            'cupos_maximos', 'cupos_disponibles', 'cupos_ocupados',
            'precio', 'prerequisitos', 'activo', 'destacado',
            'esta_disponible', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'codigo', 'coordinador', 'cupos_disponibles', 'created_at', 'updated_at', 'cupos_ocupados', 'esta_disponible']

    def validate(self, attrs):
        # Validaciones de fechas
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        fecha_limite = attrs.get('fecha_limite_inscripcion', getattr(self.instance, 'fecha_limite_inscripcion', None))

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError({'fecha_fin': 'La fecha de fin debe ser posterior a la de inicio.'})

        if fecha_limite and fecha_inicio and fecha_limite >= fecha_inicio:
            raise serializers.ValidationError({'fecha_limite_inscripcion': 'La fecha límite debe ser anterior al inicio del curso.'})

        # Validar cupos
        cupos_maximos = attrs.get('cupos_maximos', getattr(self.instance, 'cupos_maximos', None))
        if self.instance and cupos_maximos and cupos_maximos < self.instance.cupos_ocupados:
            raise serializers.ValidationError({'cupos_maximos': 'No puede reducir cupos máximos por debajo de los ya ocupados.'})

        return attrs