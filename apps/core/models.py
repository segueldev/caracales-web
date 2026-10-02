"""
=============================================================================
MODELOS BASE - ACADEMIA FELINA FLOPPA
=============================================================================
Modelos abstractos y utilidades compartidas por todas las apps.
Incluye: TimeStampedModel (created_at, updated_at), SoftDeleteModel.
=============================================================================
"""
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Modelo abstracto que añade campos de auditoría temporal.
    Todos los modelos del proyecto deben heredar de este para trazabilidad.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación',
        help_text='Timestamp automático al crear el registro'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización',
        help_text='Timestamp automático al modificar el registro'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Modelo abstracto para eliminación lógica (soft delete).
    Los registros no se borran físicamente, solo se marcan como eliminados.
    Útil para mantener integridad referencial en órdenes/matrículas históricas.
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Eliminado lógicamente',
        help_text='Marca si el registro fue eliminado (soft delete)'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de eliminación',
        help_text='Timestamp cuando se realizó el soft delete'
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Override delete para soft delete"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self):
        """Eliminación física real - usar con precaución"""
        super().delete()

    def restore(self):
        """Restaurar un registro soft-deleted"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class ActiveManager(models.Manager):
    """Manager que filtra solo registros no eliminados (activos)"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager que incluye todos los registros (incluyendo eliminados)"""
    pass