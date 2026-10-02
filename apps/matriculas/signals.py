"""
=============================================================================
SEÑALES MATRÍCULAS - ACADEMIA FELINA FLOPPA
=============================================================================
Señales para integridad referencial, validaciones automáticas.
=============================================================================
"""
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from apps.matriculas.models import CarroMatricula, ItemCarro, OrdenMatricula, MatriculaDetalle


@receiver(pre_delete, sender=CarroMatricula)
def validar_eliminacion_carro(sender, instance, **kwargs):
    """Evitar eliminación si tiene items (usar limpiar() en su lugar)"""
    if instance.items.exists():
        raise ValueError("No se puede eliminar carro con items. Use limpiar() primero.")


@receiver(post_delete, sender=ItemCarro)
def actualizar_totales_carro(sender, instance, **kwargs):
    """Los totales se calculan dinámicamente via properties, no se guardan"""
    pass


@receiver(pre_delete, sender=OrdenMatricula)
def validar_eliminacion_orden(sender, instance, **kwargs):
    """Solo permitir soft delete para órdenes (historial)"""
    if instance.estado in [OrdenMatricula.Estado.PAGADO, OrdenMatricula.Estado.ENTREGADO]:
        raise ValueError("No se puede eliminar orden pagada/entregada. Use soft delete.")