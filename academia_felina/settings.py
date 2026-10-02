"""
=============================================================================
CONFIGURACIÓN PRINCIPAL DE DJANGO - ACADEMIA FELINA FLOPPA
=============================================================================
Proyecto: Evaluación EVA 2 Backend - Unidad 2
Asignatura: Programación Back End - Desarrollo Backend
Alumno: Benjamín Seguel
Carrera: Ingeniería en Ciberseguridad
Sección: TI3041/IEC-N4-C1/D Temuco IEC
Profesor: Marcelo Patricio Alvarado Aravena
Año: 2026

Configuración para PostgreSQL, JWT con roles, DRF, Swagger, Filtros.
=============================================================================
"""

import os
from pathlib import Path
from decouple import config

# -----------------------------------------------------------------------------
# BASE PATHS
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# SECURITY SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# -----------------------------------------------------------------------------
# APPLICATION DEFINITION
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',

    # Local apps
    'apps.core',           # Modelos base, utilidades, permisos personalizados
    'apps.academico',      # Áreas, Cursos, Cupos (Catálogo público)
    'apps.matriculas',     # Carro de matrícula persistente, Órdenes, Matrículas
    'apps.usuarios',       # Usuario personalizado, roles, autenticación JWT
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'academia_felina.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Context processor personalizado para datos del alumno en footer
                'apps.core.context_processors.datos_alumno',
            ],
        },
    },
]

WSGI_APPLICATION = 'academia_felina.wsgi.application'

# -----------------------------------------------------------------------------
# DATABASE - POSTGRESQL (OBLIGATORIO SEGÚN PAUTA - NO SQLITE)
# -----------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='academia_felina'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,
    }
}

# -----------------------------------------------------------------------------
# CUSTOM USER MODEL
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

# -----------------------------------------------------------------------------
# PASSWORD VALIDATION
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------------
# INTERNATIONALIZATION
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# STATIC & MEDIA FILES
# -----------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# DEFAULT AUTO FIELD
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------------------------
# DJANGO REST FRAMEWORK CONFIGURATION
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Autenticación por defecto: JWT
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Permisos por defecto: permitir lectura pública, requerir auth para escritura
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Filtrado con django-filter
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Esquema OpenAPI/Swagger con drf-spectacular
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Formato de fechas
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M',
    'DATE_FORMAT': '%d/%m/%Y',
}

# -----------------------------------------------------------------------------
# SIMPLE JWT CONFIGURATION - CON CLAIMS PERSONALIZADOS (ROL)
# -----------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': config('JWT_ROTATE_REFRESH_TOKENS', default=True, cast=bool),
    'BLACKLIST_AFTER_ROTATION': config('JWT_BLACKLIST_AFTER_ROTATION', default=True, cast=bool),
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# -----------------------------------------------------------------------------
# DRF SPECTACULAR (SWAGGER/OPENAPI) CONFIGURATION
# -----------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'Academia Felina Floppa API',
    'DESCRIPTION': '''
    API REST para la Academia de Entrenamiento Felino "Floppa".
    
    **Roles y Permisos:**
    - **PÚBLICO**: Catálogo de cursos y áreas (GET)
    - **ESTUDIANTE**: Carro de matrícula, checkout, mis matrículas (JWT requerido)
    - **COORDINADOR**: Gestión completa de cursos, cambio de estados de matrículas (JWT + rol admin)
    
    **Flujo de Matrícula:**
    1. Estudiante agrega cursos al carro persistente (1:1 Usuario-Carro)
    2. Checkout valida cupos disponibles atómicamente
    3. Al confirmar PAGADO: descuenta cupos, genera matrículas oficiales
    4. Si CANCELADO: libera cupos automáticamente
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'TAGS': [
        {'name': 'Autenticación', 'description': 'Login, refresh, registro, perfil'},
        {'name': 'Catálogo Público', 'description': 'Áreas y Cursos (lectura pública)'},
        {'name': 'Carro de Matrícula', 'description': 'Persistente, vinculado al usuario (Estudiante)'},
        {'name': 'Matrículas/Órdenes', 'description': 'Checkout, historial, cambio de estados (Coordinador)'},
    ],
    'CONTACT': {
        'name': 'Benjamín Seguel',
        'email': 'benjamin.seguel@inacap.cl',
    },
    'LICENSE': {
        'name': 'Evaluación Académica EVA 2 - INACAP Temuco 2026',
    },
    'SECURITY': [{'Bearer': []}],
}

# -----------------------------------------------------------------------------
# CONFIGURACIÓN PERSONALIZADA DEL PROYECTO
# -----------------------------------------------------------------------------
# Datos del alumno para footer/base templates (requerido por pauta)
DATOS_ALUMNO = {
    'nombre_completo': 'Benjamín Seguel',
    'carrera': 'Ingeniería en Ciberseguridad',
    'seccion': 'TI3041/IEC-N4-C1/D Temuco IEC',
    'profesor': 'Marcelo Patricio Alvarado Aravena',
    'anio': 2026,
    'evaluacion': 'EVA 2 Backend - Unidad 2',
}

# Configuración de la temática
TEMATICA = {
    'nombre_sistema': 'Academia Felina Floppa',
    'eslogan': 'Entrenamiento de élite para caracales',
    'mascota': 'Floppa (Caracal caracal)',
}