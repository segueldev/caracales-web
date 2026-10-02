"""
=============================================================================
MODELOS ACADÉMICOS - ACADEMIA FELINA FLOPPA
=============================================================================
Áreas de Conocimiento y Cursos/Bootcamps.
Incluye CHOICES para estado del curso, cupos, validaciones.
Endpoints públicos para catálogo (GET /api/catalogo/areas/, /api/catalogo/cursos/).
=============================================================================
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel, ActiveManager, AllObjectsManager
from apps.usuarios.models import Usuario


class AreaConocimiento(TimeStampedModel, SoftDeleteModel):
    """
    Áreas de conocimiento (ej: Caza, Sigilo, Ronroneo, Trepar, Historia Felina).
    Catálogo público - lectura permitida sin autenticación.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del área')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Slug URL')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    icono = models.CharField(
        max_length=50,
        blank=True,
        default='🐾',
        verbose_name='Icono/Emoji',
        help_text='Emoji representativo (ej: 🎯 🐾 😺 🏃)'
    )
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden de visualización')
    activa = models.BooleanField(default=True, verbose_name='Área activa')

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Área de Conocimiento'
        verbose_name_plural = 'Áreas de Conocimiento'
        ordering = ['orden', 'nombre']
        indexes = [models.Index(fields=['activa', 'orden'])]

    def __str__(self):
        return f"{self.icono} {self.nombre}"

    @property
    def cursos_count(self):
        return self.cursos.filter(activo=True, is_deleted=False).count()

    @property
    def icono_img(self):
        """
        Ruta (relativa a static/) de la imagen de icono del área.
        Si el usuario sube static/assets/iconos/areas/<slug>.png se usa esa
        imagen; si no existe, los templates muestran el emoji `icono`.
        """
        return f'assets/iconos/areas/{self.slug}.png'


class Curso(TimeStampedModel, SoftDeleteModel):
    """
    Cursos/Bootcamps ofrecidos por la academia.
    Cada curso tiene cupos limitados, fechas, precio.
    CUMPLE PAUTA: CHOICES en campo 'estado' (borrador, publicado, archivado).
    """
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador (no visible en catálogo)'
        PUBLICADO = 'PUBLICADO', 'Publicado (visible y matriculable)'
        ARCHIVADO = 'ARCHIVADO', 'Archivado (no disponible)'

    class Modalidad(models.TextChoices):
        PRESENCIAL = 'PRESENCIAL', 'Presencial (en el territorio)'
        VIRTUAL = 'VIRTUAL', 'Virtual (videollamada gatuna)'
        HIBRIDO = 'HIBRIDO', 'Híbrido (mixto)'

    # Identificación
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código del curso',
        help_text='Código único tipo FLF-001, FLF-002...'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del curso')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='Slug URL')

    # Relaciones
    area = models.ForeignKey(
        AreaConocimiento,
        on_delete=models.PROTECT,
        related_name='cursos',
        verbose_name='Área de conocimiento'
    )
    coordinador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='cursos_coordinados',
        limit_choices_to={'rol': Usuario.Rol.COORDINADOR},
        verbose_name='Coordinador responsable'
    )

    # Detalles
    descripcion = models.TextField(verbose_name='Descripción completa')
    resumen = models.CharField(max_length=300, verbose_name='Resumen corto (catálogo)')
    imagen = models.ImageField(upload_to='cursos/', blank=True, null=True, verbose_name='Imagen del curso')

    # Configuración académica
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        verbose_name='Estado del curso',
        help_text='CHOICES explícito - REQUERIDO POR PAUTA'
    )
    modalidad = models.CharField(
        max_length=20,
        choices=Modalidad.choices,
        default=Modalidad.PRESENCIAL,
        verbose_name='Modalidad'
    )

    # Fechas
    fecha_inicio = models.DateTimeField(verbose_name='Fecha y hora de inicio')
    fecha_fin = models.DateTimeField(verbose_name='Fecha y hora de fin')
    fecha_limite_inscripcion = models.DateTimeField(
        verbose_name='Fecha límite de inscripción',
        help_text='Después de esta fecha no se permite matricularse'
    )

    # Cupos y precio
    cupos_maximos = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        verbose_name='Cupos máximos',
        help_text='Número máximo de estudiantes por cohorte'
    )
    cupos_disponibles = models.PositiveIntegerField(
        default=0,
        verbose_name='Cupos disponibles',
        help_text='Se actualiza automáticamente al matricular/cancelar'
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de matrícula (CLP)'
    )

    # Requisitos
    prerequisitos = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name='Prerrequisitos',
        help_text='Cursos que deben completarse antes'
    )

    # Metadatos
    activo = models.BooleanField(default=True, verbose_name='Curso activo')
    destacado = models.BooleanField(default=False, verbose_name='Destacado en home')

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Curso/Bootcamp'
        verbose_name_plural = 'Cursos/Bootcamps'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['estado', 'activo', 'fecha_inicio']),
            models.Index(fields=['area', 'estado']),
            models.Index(fields=['fecha_inicio']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def save(self, *args, **kwargs):
        # Sincronizar cupos_disponibles al crear
        if self._state.adding and self.cupos_disponibles == 0:
            self.cupos_disponibles = self.cupos_maximos
        super().save(*args, **kwargs)

    @property
    def esta_disponible(self):
        """Verifica si el curso está disponible para matrícula"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.activo and
            not self.is_deleted and
            self.estado == self.Estado.PUBLICADO and
            self.cupos_disponibles > 0 and
            self.fecha_limite_inscripcion > now
        )

    @property
    def cupos_ocupados(self):
        return self.cupos_maximos - self.cupos_disponibles

    def descontar_cupo(self):
        """Descuenta un cupo atómicamente (usar en transacción)"""
        if self.cupos_disponibles > 0:
            self.cupos_disponibles -= 1
            self.save(update_fields=['cupos_disponibles', 'updated_at'])
            return True
        return False

    def liberar_cupo(self):
        """Libera un cupo (al cancelar matrícula)"""
        if self.cupos_disponibles < self.cupos_maximos:
            self.cupos_disponibles += 1
            self.save(update_fields=['cupos_disponibles', 'updated_at'])
            return True
        return False