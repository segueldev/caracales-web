# =============================================================================
# CORE APP CONFIG - ACADEMIA FELINA FLOPPA
# =============================================================================
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core - Utilidades y Base'

    def ready(self):
        # Importar señales si existen
        try:
            import apps.core.signals  # noqa: F401
        except ImportError:
            pass