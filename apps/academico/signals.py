"""
=============================================================================
SEÑALES ACADÉMICAS - ACADEMIA FELINA FLOPPA
=============================================================================
Señales para mantener integridad de cupos, validaciones, etc.
=============================================================================
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.academico.models import Curso


@receiver(pre_save, sender=Curso)
def validar_curso_pre_save(sender, instance, **kwargs):
    """Validaciones antes de guardar curso"""
    # Generar código automático si no existe
    if not instance.codigo:
        from django.utils.text import slugify
        base = slugify(instance.nombre)[:10].upper()
        import uuid
        instance.codigo = f"FLF-{base}-{str(uuid.uuid4())[:4].upper()}"


@receiver(post_save, sender=Curso)
def sincronizar_cupos_post_save(sender, instance, created, **kwargs):
    """Sincronizar cupos_disponibles al crear"""
    if created and instance.cupos_disponibles == 0:
        instance.cupos_disponibles = instance.cupos_maximos
        instance.save(update_fields=['cupos_disponibles'])