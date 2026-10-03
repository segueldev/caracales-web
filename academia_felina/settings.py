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
# POR QUÉ POSTGRESQL Y NO SQLITE:
# La pauta exige "Configuración nativa con PostgreSQL o MySQL (no SQLite)".
# SQLite guarda todo en un único archivo y trabaja con bloqueo de archivo
# completo; eso no sirve para demostrar el CONTROL CONCURRENTE de cupos que
# evalúa esta prueba. PostgreSQL sí ofrece bloqueo a nivel de FILA, que es lo
# que aprovecha `select_for_update()` en apps/matriculas/services.py.
#
# CADA CLAVE:
#   ENGINE        -> driver oficial de Django (módulo django.db.backends.postgresql,
#                    que habla con el servidor por libpq / psycopg).
#   NAME          -> nombre de la BD creada con `createdb academia_felina`.
#   USER/PASSWORD -> credenciales del rol de PostgreSQL (no las de superusuario
#                    de Django: esas son del admin de /admin/).
#   HOST/PORT     -> 127.0.0.1:5432 (por defecto de la instalación).
#   CONN_MAX_AGE  -> "conexión persistente": reutiliza la misma conexión TCP
#                    entre peticiones durante 60 s en vez de abrir y cerrar una
#                    por request. Baja la latencia y es el motivo por el que
#                    una segunda petición responde más rápido.
#   connect_timeout -> evita que la app se cuelgue si PostgreSQL no está arriba.
#
# TODOS LOS VALORES VIVEN EN EL ARCHIVO `.env` (python-decouple), por lo que
# NO hay credenciales duras en el código. Se copia de `.env.example`.
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

# Debe empezar y terminar con '/': si no, `imagen.url` devuelve una ruta
# RELATIVA y las fotos de curso se rompen en cualquier página que no sea la raíz
# (en /catalogo/ el navegador pediría /catalogo/media/... y daría 404).
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# DEFAULT AUTO FIELD
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------------------------
# DJANGO REST FRAMEWORK CONFIGURATION
# -----------------------------------------------------------------------------
# Configuración GLOBAL: aplica a todos los ViewSets salvo que la sobrescriban
# con `authentication_classes`, `permission_classes` o `filter_backends` a nivel
# de clase (que es como se hace el RBAC en este proyecto).
REST_FRAMEWORK = {
    # Autenticación por defecto: JWT.
    # DRF lee la cabecera `Authorization: Bearer <token>` y, si el token es
    # válido, rellena `request.user` con el Usuario del claim `user_id`.
    # SIN esto, `request.user` sería AnonymousUser y todos los permisos fallarían.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    # Permisos por defecto: AllowAny.
    # DECISIÓN DE DISEÑO IMPORTANTE: el permiso por defecto es abierto para que
    # el catálogo sea consultable sin login (pauta: "Endpoints de lectura pública
    # para catálogo/oferta"). La RESTRICCIÓN REAL no está aquí sino en cada
    # ViewSet vía get_permissions() -> IsCoordinador / IsEstudiante (RBAC).
    # Si se dejara IsAuthenticated global, el catálogo pediría token y el
    # visitante anónimo no vería nada.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Filtrado con django-filter (pauta E: "Sistema de filtros aplicado sobre
    # campos clave del modelo"). Los ViewSets lo habilitan declarando
    # `filterset_class = CursoFilter`; aquí queda el backend disponible.
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Paginación: los listados devuelven {count, next, previous, results}
    # con 20 ítems por página, en vez de volcar toda la tabla.
    # Se usa el paginador propio porque además acepta ?page_size=, lo que el
    # catálogo necesita para pedir de a 10 filas (ver apps/core/paginators.py).
    'DEFAULT_PAGINATION_CLASS': 'apps.core.paginators.PaginacionEstandar',
    'PAGE_SIZE': 20,
    # Esquema OpenAPI/Swagger con drf-spectacular (pauta: "Soporte de
    # Documentación API: Swagger / OpenAPI"). Genera /api/schema/ (JSON/YAML)
    # y lo consume /api/docs/ (Swagger UI).
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # ---------------------------------------------------------------------
    # FORMATO DE FECHAS - BUG CORREGIDO
    # ---------------------------------------------------------------------
    # Estaba en '%d/%m/%Y %H:%M', es decir "01/11/2026 01:52" (orden chileno).
    # El front hace `new Date(valor)`, y JavaScript SIEMPRE interpreta
    # MM/DD/AAAA (mes primero). Con eso la API producía DOS defectos distintos:
    #
    #   * Día > 12 -> mes 23 es imposible -> "Invalid Date" en pantalla.
    #     (FLF-005, con fecha real 23-10-2026, mostraba literalmente "Invalid Date")
    #   * Día <= 12 -> lo interpretaba al revés y mentía EN SILENCIO.
    #     (FLF-004, real 1-nov-2026, se veía 11-ene-2026)
    #
    # Además el propio esquema OpenAPI que publicamos en /api/schema/ ya
    # declaraba `format: date-time` (RFC 3339) para fecha_inicio, created_at,
    # fecha_pago... o sea que la documentación contradecía la implementación.
    #
    # Se usa el valor por defecto de DRF: ISO 8601 / RFC 3339
    # ("2026-11-01T04:52:24+00:00"), que es el estándar de un API REST y es
    # lo que new Date() parsea sin ambigüedad. La presentación local
    # (dd-mm-aaaa) es responsabilidad de la interfaz, en fechaHTML() de
    # static/js/main.js: un API entrega datos, no formato de vitrina.
    'DATETIME_FORMAT': 'iso-8601',
    'DATE_FORMAT': 'iso-8601',
}

# -----------------------------------------------------------------------------
# SIMPLE JWT CONFIGURATION - CON CLAIMS PERSONALIZADOS (ROL)
# -----------------------------------------------------------------------------
# CICLO DE VIDA DEL TOKEN
#   login -> access (60 min) + refresh (7 días)
#   access expira -> POST /api/auth/refresh/ devuelve un access nuevo
#   logout/rotación -> el refresh se BLACKLISTEA y deja de servir.
#
# CLAVES QUE IMPORTAN PARA LA DEFENSA:
#   ACCESS_TOKEN_LIFETIME  -> caducidad corta del token de uso diario.
#   REFRESH_TOKEN_LIFETIME -> caducidad larga del "pase de renovación".
#   ROTATE_REFRESH_TOKENS  -> en cada refresh se emite un refresh NUEVO y el
#                             viejo se invalida (si lo roban, sólo sirve una vez).
#   BLACKLIST_AFTER_ROTATION -> el refresh anterior queda registrado en la tabla
#                             `token_blacklist_outstandingtoken` (app
#                             `token_blacklist` instalada arriba).
#   ALGORITHM HS256        -> firma HMAC-SHA256 con SECRET_KEY. El payload NO
#                             va cifrado: cualquiera puede LEERLO (base64), pero
#                             NADIE puede FALSIFICARLO sin la clave.
#   AUTH_HEADER_TYPES       -> exige el prefijo "Bearer".
#   USER_ID_CLAIM          -> Django busca ese claim para reconstruir request.user.
#   JTI_CLAIM              -> identificador único del token, base del blacklist.
#
# El claim `rol` NO se agrega aquí sino en apps/usuarios/tokens.py
# (CustomAccessToken / CustomRefreshToken), porque necesita leer el modelo
# Usuario y eso no corresponde en settings.
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
    # ---------------------------------------------------------------------------
    # NOMBRADO DE ENUMS
    # ---------------------------------------------------------------------------
    # Los CHOICES del proyecto se llaman igual en varios modelos
    # (`Curso.Estado`, `OrdenMatricula.Estado`, ambos usados en campos
    # llamados "estado"). Sin este mapa, drf-spectacular no puede decidir a
    # qué componente pertenece cada conjunto y genera nombres crípticos
    # como `Estado793Enum` / `Estado5a1Enum`, que no se pueden defender en la
    # defensa oral. Aquí cada CHOICES queda con un nombre único y estable:
    # el esquema dice `EstadoCurso` y `EstadoOrden` y se distinguen al tocar.
    'ENUM_NAME_OVERRIDES': {
        'EstadoCurso': 'apps.academico.models.Curso.Estado',
        'EstadoOrden': 'apps.matriculas.models.OrdenMatricula.Estado',
        'ModalidadCurso': 'apps.academico.models.Curso.Modalidad',
        'RolUsuario': 'apps.usuarios.models.Usuario.Rol',
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