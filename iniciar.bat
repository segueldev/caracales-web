@echo off
setlocal enabledelayedexpansion
REM =============================================================================
REM ACADEMIA FELINA FLOPPA - INICIO DEL PROYECTO (Windows)
REM =============================================================================
REM Uso: doble clic en este archivo, o desde una terminal (CMD/PowerShell):
REM
REM     iniciar.bat
REM
REM Hace lo mismo que iniciar.sh pero en Windows:
REM   1. Crea y activa el entorno virtual venv\
REM   2. Instala requirements.txt
REM   3. Copia .env.example a .env si no existe
REM   4. Comprueba/crea la base de datos PostgreSQL
REM   5. Aplica migraciones y datos de demostracion
REM   6. Arranca el servidor en http://127.0.0.1:8000/
REM =============================================================================
cd /d "%~dp0"
color 0A
echo ===============================================================
echo   Academia Felina Floppa - EVA 2 Backend (Windows)
echo   Carpeta: %CD%
echo ===============================================================
echo.

REM --- 1. Localizar Python ----------------------------------------------------
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (
    where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
    color 0C
    echo [ERROR] No se encontro Python en el PATH.
    echo         Descargalo desde https://www.python.org/downloads/
    echo         IMPORTANTE: marca la casilla "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)
echo [OK] Usando: %PY%

REM --- 2. Entorno virtual -----------------------------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo [AVISO] Creando el entorno virtual por primera vez...
    %PY% -m venv venv
    if errorlevel 1 (
        color 0C
        echo [ERROR] No se pudo crear venv\
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
echo [OK] Entorno virtual activado

REM --- 3. Dependencias --------------------------------------------------------
python -c "import django, rest_framework, rest_framework_simplejwt, django_filters, drf_spectacular, psycopg" >nul 2>nul
if errorlevel 1 (
    echo [AVISO] Instalando dependencias de requirements.txt...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        color 0C
        echo [ERROR] Fallo la instalacion de dependencias.
        echo         Revisa tu conexion a internet y vuelve a ejecutar iniciar.bat
        pause
        exit /b 1
    )
)
python -c "import django; print('[OK] Django', django.get_version())"

REM --- 4. Archivo .env --------------------------------------------------------
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [AVISO] Se creo .env desde .env.example
    echo         Abre .env con el Bloc de notas y pon ahi tu contrasena de PostgreSQL.
)

REM Cargar variables del .env para este proceso (for /f lee linea por linea)
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "LINEA=%%A"
    if not "!LINEA:~0,1!"=="#" if not "!LINEA!"=="" (
        set "%%A=%%B"
    )
)

if "%DB_NAME%"=="" set "DB_NAME=academia_felina"
if "%DB_USER%"=="" set "DB_USER=postgres"
if "%DB_PASSWORD%"=="" set "DB_PASSWORD=postgres"
if "%DB_HOST%"=="" set "DB_HOST=localhost"
if "%DB_PORT%"=="" set "DB_PORT=5432"

REM --- 5. PostgreSQL ----------------------------------------------------------
set "PSQL="
where psql >nul 2>nul && set "PSQL=psql"
REM Buscar instalacion por defecto (PostgreSQL 13 a 18)
if not defined PSQL (
    for %%V in (18 17 16 15 14 13) do (
        if exist "C:\Program Files\PostgreSQL\%%V\bin\psql.exe" set "PSQL=C:\Program Files\PostgreSQL\%%V\bin\psql.exe"
    )
)

if defined PSQL (
    "%PSQL%" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d postgres -tAc "select 1" >nul 2>nul
    if errorlevel 1 (
        color 0C
        echo [ERROR] No se pudo conectar a PostgreSQL como usuario "%DB_USER%".
        echo         Revisa DB_USER y DB_PASSWORD dentro de .env
        echo         (no es lo mismo el usuario de PostgreSQL que el de /admin/ de Django)
        pause
        exit /b 1
    )
    echo [OK] PostgreSQL responde en %DB_HOST%:%DB_PORT%

    REM Intentar crear la BD. Si ya existe, psql devuelve error y NO importa:
    REM la verificacion posterior es la que realmente decide si seguimos.
    "%PSQL%" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d postgres -c "CREATE DATABASE %DB_NAME%;" >nul 2>nul

    REM Verificar que se pueda ABRIR la base de datos (si no existe, falla aqui)
    "%PSQL%" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -tAc "select 1" >nul 2>nul
    if errorlevel 1 (
        color 0C
        echo [ERROR] No existe la base de datos "%DB_NAME%" y no se pudo crear.
        echo         Creala a mano desde pgAdmin o con:
        echo             CREATE DATABASE %DB_NAME%;
        echo         y revisa DB_USER / DB_PASSWORD dentro de .env
        pause
        exit /b 1
    )
    echo [OK] Base de datos "%DB_NAME%" disponible
) else (
    echo [AVISO] No se encontro psql en el PATH ni en C:\Program Files\PostgreSQL
    echo         Si la BD no existe, la creacion fallara. Continuo igual...
)

REM --- 6. Migraciones --------------------------------------------------------
echo.
echo --- Aplicando migraciones ---
python manage.py migrate --noinput
if errorlevel 1 (
    color 0C
    echo [ERROR] Fallaron las migraciones.
    pause
    exit /b 1
)
echo [OK] Tablas al dia en PostgreSQL

REM --- 7. Datos de demostracion (solo la primera vez) -------------------------
echo.
set "CUPOS=0"
REM `manage.py shell -c` imprime tambien una linea "(N objects imported...)",
REM por eso SÓLO se acepta lo que sea puramente numerico.
for /f %%N in ('python manage.py shell -c "from apps.academico.models import Curso; print(Curso.objects.count())" 2^>nul') do (
    echo %%N| findstr /r "^[0-9][0-9]*$" >nul && set "CUPOS=%%N"
)
if "%CUPOS%"=="0" (
    echo --- Cargando datos de demostracion ---
    python manage.py poblar_demo
    echo [OK] Datos de prueba cargados
) else (
    echo [OK] La BD ya tiene cursos (%CUPOS%): no se recarga la demo
)

REM --- 8. Servidor ------------------------------------------------------------
echo.
echo ===============================================================
echo [OK] TODO LISTO
echo   Sitio web : http://127.0.0.1:8000/
echo   Swagger   : http://127.0.0.1:8000/api/docs/
echo   Admin     : http://127.0.0.1:8000/admin/
echo.
echo   Coordinador : coordinador / coordinador123
echo   Estudiante  : estudiante1 / floppa123
echo   Para detener el servidor: Ctrl + C  (o cierra esta ventana)
echo ===============================================================
echo.
python manage.py runserver 0.0.0.0:8000

pause
