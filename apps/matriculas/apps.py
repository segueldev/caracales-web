# =============================================================================
# MATRICULAS APP CONFIG - ACADEMIA FELINA FLOPPA
# =============================================================================
from django.apps import AppConfig


class MatriculasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.matriculas'
    verbose_name = 'Matrículas y Carro de Compras'

    def ready(self):
        import apps.matriculas.signals  # noqa: F401