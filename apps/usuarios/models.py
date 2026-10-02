"""
=============================================================================
MODELO DE USUARIO PERSONALIZADO - ACADEMIA FELINA FLOPPA
=============================================================================
Extendiendo AbstractUser para añadir rol (CHOICES obligatorio según pauta).
Roles: ESTUDIANTE (cliente) vs COORDINADOR (admin/gestor).
Incluye campos adicionales: teléfono, avatar, biografía.
=============================================================================
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class Usuario(AbstractUser, TimeStampedModel):
    """
    Usuario personalizado con roles para RBAC (Role-Based Access Control).
    
    CHOICES explícito en campo 'rol' - REQUERIDO POR PAUTA:
    "Implementación explícita de al menos una propiedad CHOICES en el modelo"
    """
    class Rol(models.TextChoices):
        ESTUDIANTE = 'ESTUDIANTE', _('Estudiante (Cliente)')
        COORDINADOR = 'COORDINADOR', _('Coordinador Académico (Admin/Gestor)')

    # Campo rol con CHOICES - CUMPLE REQUERIMIENTO DE PAUTA
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ESTUDIANTE,
        verbose_name='Rol del usuario',
        help_text='Define permisos: Estudiante (carro, matrículas) vs Coordinador (gestión cursos, estados)'
    )

    # Campos adicionales del perfil
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono de contacto'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Foto de perfil',
        help_text='Imagen opcional del usuario (caracal preferentemente)'
    )
    biografia = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Biografía',
        help_text='Breve descripción del caracal/estudiante'
    )
    fecha_nacimiento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de nacimiento'
    )

    # Configuración de notificaciones
    email_notificaciones = models.BooleanField(
        default=True,
        verbose_name='Recibir notificaciones por email'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['rol']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_estudiante(self):
        """Verifica si el usuario es estudiante"""
        return self.rol == self.Rol.ESTUDIANTE

    @property
    def es_coordinador(self):
        """Verifica si el usuario es coordinador"""
        return self.rol == self.Rol.COORDINADOR

    def get_carrito_activo(self):
        """
        Obtiene o crea el carro de matrícula activo del estudiante.
        Relación 1:1 Usuario-Carro (requerido por pauta: 'Persistencia del Carro').
        """
        if not self.es_estudiante:
            return None
        from apps.matriculas.models import CarroMatricula
        carro, _ = CarroMatricula.objects.get_or_create(estudiante=self, activo=True)
        return carro