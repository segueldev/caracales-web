"""
=============================================================================
SEÑALES USUARIOS - ACADEMIA FELINA FLOPPA
=============================================================================
Señales post_save para crear perfil relacionado, carro de matrícula, etc.
=============================================================================
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.usuarios.models import Usuario


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_recursos_usuario(sender, instance, created, **kwargs):
    """
    Al crear usuario estudiante, crear su carro de matrícula persistente (1:1).
    CUMPLE PAUTA: "Relación 1 a 1 entre el Usuario y su Carro activo en base de datos"
    """
    if created and instance.es_estudiante:
        from apps.matriculas.models import CarroMatricula
        CarroMatricula.objects.get_or_create(estudiante=instance, activo=True)