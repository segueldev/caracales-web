# =============================================================================
# ACADEMICO APP CONFIG - ACADEMIA FELINA FLOPPA
# =============================================================================
from django.apps import AppConfig


class AcademicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.academico'
    verbose_name = 'Catálogo Académico'

    def ready(self):
        import apps.academico.signals  # noqa: F401