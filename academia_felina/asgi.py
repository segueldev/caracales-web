"""
=============================================================================
ASGI CONFIG - ACADEMIA FELINA FLOPPA
=============================================================================
Punto de entrada para servidores ASGI (Daphne, Uvicorn, etc.)
=============================================================================
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academia_felina.settings')
application = get_asgi_application()