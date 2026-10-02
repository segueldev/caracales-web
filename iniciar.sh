#!/usr/bin/env bash
# =============================================================================
# ACADEMIA FELINA FLOPPA — INICIO DEL PROYECTO (Linux / macOS)
# =============================================================================
# Este script deja el proyecto listo y corriendo con UN SOLO comando:
#
#     ./iniciar.sh
#
# Qué hace, en orden:
#   1. Detecta Python 3.
#   2. Crea el entorno virtual `venv/` si no existe y activa.
#   3. Instala requirements.txt (Django, DRF, SimpleJWT, django-filter,
#      drf-spectacular, psycopg para PostgreSQL, Pillow).
#   4. Copia `.env.example` a `.env` si es la primera vez.
#   5. Comprueba que PostgreSQL esté encendido y que exista la base de datos.
#   6. Aplica las migraciones (crea las tablas).
#   7. Carga datos de demostración sólo si la tabla de cursos está vacía.
#   8. Arranca el servidor de desarrollo en http://127.0.0.1:8000/
#
# Si algo falla, el script se detiene con un mensaje y NO sigue a medias.
# Para reanudar, simplemente vuelve a ejecutar `./iniciar.sh`.
# =============================================================================
set -u   # variable sin definir = error (evita continuar con valores vacíos)

# --- Colores para que los mensajes se distingan en la terminal ---------------
VERDE="\033[0;32m"; AMARILLO="\033[1;33m"; ROJO="\033[0;31m"; SIN="\033[0m"

info()  { echo -e "${VERDE}[OK]${SIN} $1"; }
aviso() { echo -e "${AMARILLO}[AVISO]${SIN} $1"; }
error() { echo -e "${ROJO}[ERROR]${SIN} $1"; }

# --- 0. Trabajar SIEMPRE desde la carpeta del script ------------------------
cd "$(dirname "$0")" || { error "No se pudo entrar al directorio del proyecto."; exit 1; }
echo "==============================================================="
echo "  Academia Felina Floppa — EVA 2 Backend"
echo "  Carpeta: $(pwd)"
echo "==============================================================="

# --- 1. Python ---------------------------------------------------------------
PY=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1; then
        PY="$candidato"
        break
    fi
done

if [ -z "$PY" ]; then
    error "No se encontró Python."
    echo "  EndeavourOS / Arch Linux : sudo pacman -S python python-pip"
    echo "  Debian / Ubuntu          : sudo apt install python3 python3-venv"
    exit 1
fi

PY_VERSION=$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python $PY_VERSION en $(command -v "$PY")"

# Django 5.2 exige Python 3.10 o superior
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    error "Se requiere Python 3.10 o superior (hay $PY_VERSION)."
    exit 1
}

# --- 2. Entorno virtual ------------------------------------------------------
if [ ! -f "venv/bin/activate" ]; then
    aviso "Creando el entorno virtual por primera vez (esto tarda un poco)..."
    "$PY" -m venv venv || { error "No se pudo crear venv/."; exit 1; }
fi
# shellcheck disable=SC1091
source venv/bin/activate || { error "No se pudo activar venv/."; exit 1; }
info "Entorno virtual activado (venv/)"

# --- 3. Dependencias ---------------------------------------------------------
if ! python -c "import django, rest_framework, rest_framework_simplejwt, django_filters, drf_spectacular, psycopg" 2>/dev/null; then
    aviso "Instalando dependencias de requirements.txt..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt || {
        error "Falló la instalación de dependencias."
        echo "  Revisa la conexión a internet y vuelve a ejecutar ./iniciar.sh"
        exit 1
    }
fi
info "Dependencias instaladas ($(python -c 'import django; print(django.get_version())') de Django)"

# --- 4. Archivo .env ---------------------------------------------------------
if [ ! -f ".env" ]; then
    cp .env.example .env
    aviso "Se creó .env desde .env.example."
    aviso "EDITA .env y pon ahí tu contraseña de PostgreSQL antes de continuar."
    echo "         nano .env"
    echo
fi

# Cargar variables de entorno del .env (sin exportarlas fuera de este script)
set -a
# shellcheck disable=SC1091
. ./.env
set +a

DB_NAME="${DB_NAME:-academia_felina}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# --- 5. PostgreSQL -----------------------------------------------------------
if ! command -v psql >/dev/null 2>&1; then
    error "No se encontró el cliente de PostgreSQL (psql)."
    echo "  EndeavourOS / Arch Linux : sudo pacman -S postgresql"
    echo "  Debian / Ubuntu          : sudo apt install postgresql postgresql-client"
    echo "  Luego inicializa el cluster: sudo postgresql-setup --initialize"
    echo "  Y arranca el servicio    : sudo systemctl enable --now postgresql"
    exit 1
fi

if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
    error "PostgreSQL no responde en $DB_HOST:$DB_PORT."
    echo "  Para arrancarlo:  sudo systemctl start postgresql"
    echo "  Para que arranque siempre al encender:  sudo systemctl enable --now postgresql"
    echo "  Estado del servicio:  systemctl status postgresql"
    exit 1
fi
info "PostgreSQL responde en $DB_HOST:$DB_PORT"

# Crear la base de datos si no existe (idempotente: se puede correr muchas veces)
export PGPASSWORD="$DB_PASSWORD"
EXISTE=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc \
          "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null || echo "ERROR")

if [ "$EXISTE" = "ERROR" ]; then
    error "No pude conectarme a PostgreSQL con el usuario '$DB_USER'."
    echo "  Revisa DB_USER y DB_PASSWORD dentro de .env"
    echo "  (no es lo mismo el usuario de PostgreSQL que el de /admin/ de Django)"
    unset PGPASSWORD
    exit 1
elif [ "$EXISTE" != "1" ]; then
    aviso "Creando la base de datos '$DB_NAME'..."
    if createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres "$DB_NAME" 2>/dev/null; then
        info "Base de datos creada"
    else
        error "No se pudo crear '$DB_NAME'."
        echo "  Crédalas a mano:  createdb $DB_NAME"
        echo "  O verifica que el usuario '$DB_USER' tenga permiso CREATEDB."
        unset PGPASSWORD
        exit 1
    fi
else
    info "Base de datos '$DB_NAME' disponible"
fi
unset PGPASSWORD

# --- 6. Migraciones ----------------------------------------------------------
echo
echo "--- Aplicando migraciones ---"
python manage.py migrate --noinput || {
    error "Fallaron las migraciones."
    echo "  Suele deberse a una BD de una versión anterior: borra la BD y repite."
    exit 1
}
info "Tablas al día en PostgreSQL"

# --- 7. Datos de demostración (sólo la primera vez) --------------------------
# OJO: `manage.py shell -c` imprime también una línea tipo
# "(N objects imported automatically...)", por eso nos quedamos sólo con la
# línea que contiene un número.
CUPOS=$(python manage.py shell -c "from apps.academico.models import Curso; print(Curso.objects.count())" 2>/dev/null \
        | grep -E '^[0-9]+$' | tail -n1)
CUPOS="${CUPOS:--1}"

if [ "$CUPOS" = "0" ]; then
    echo
    echo "--- Cargando datos de demostración ---"
    python manage.py poblar_demo && info "Datos de prueba cargados"
elif [ "$CUPOS" = "-1" ]; then
    aviso "No se pudo consultar la tabla de cursos (¿migraciones pendientes?)."
else
    info "La BD ya tiene cursos ($CUPOS): no se recarga la demo"
fi

# --- 8. Servidor -------------------------------------------------------------
echo
echo "==============================================================="
info "TODO LISTO"
echo "  Sitio web : http://127.0.0.1:8000/"
echo "  Swagger   : http://127.0.0.1:8000/api/docs/"
echo "  Admin     : http://127.0.0.1:8000/admin/"
echo
echo "  Coordinador : coordinador / coordinador123"
echo "  Estudiante  : estudiante1 / floppa123"
echo "  Para detener el servidor: Ctrl + C"
echo "==============================================================="
echo
python manage.py runserver 0.0.0.0:8000
