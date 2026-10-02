"""
=============================================================================
WSGI CONFIG - ACADEMIA FELINA FLOPPA
=============================================================================
Punto de entrada para servidores WSGI (Gunicorn, uWSGI, etc.)
=============================================================================
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academia_felina.settings')
application = get_wsgi_application()