"""
=============================================================================
CONTEXT PROCESSORS - ACADEMIA FELINA FLOPPA
=============================================================================
Inyecta datos del alumno en todas las plantillas (requerido por pauta:
footer con Nombre, Sección, Año visibles en vistas HTML base).
=============================================================================
"""
from django.conf import settings


def datos_alumno(request):
    """
    Context processor que expone DATOS_ALUMNO y TEMATICA en todos los templates.
    Cumple requerimiento: 'Datos Alumno - Nombre, Sección y Año presentes en la vista/footer base'
    """
    return {
        'DATOS_ALUMNO': getattr(settings, 'DATOS_ALUMNO', {}),
        'TEMATICA': getattr(settings, 'TEMATICA', {}),
    }