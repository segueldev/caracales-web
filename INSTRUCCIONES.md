# =============================================================================
# INSTRUCCIONES DE INSTALACIÓN Y EJECUCIÓN
# Academia Felina Floppa — EVA 2 Backend (Django REST Framework + PostgreSQL)
# =============================================================================
# Este documento cubre los tres caminos oficiales para levantar el proyecto:
#
#   1. Linux (probado en EndeavourOS / Arch Linux)  -> iniciar.sh
#   2. Windows (10/11)                              -> iniciar.bat
#   3. Visual Studio Code (depuración paso a paso)  -> .vscode/
#
# Si sólo quieres que funcione:  ejecuta `./iniciar.sh` (Linux) o
# doble clic en `iniciar.bat` (Windows). Todo lo demás es detalle.
# =============================================================================


# 0. REQUISITOS PREVIOS

- Python 3.10 o superior (el proyecto está probado con Python 3.14).
- PostgreSQL 13 o superior corriendo en localhost:5432.
- Git (para clonar el repositorio).
- Opcional: Visual Studio Code con la extensión oficial **Python** de Microsoft.


# 1. LINUX (EndeavourOS / Arch Linux y derivados)

## 1.1 Paquetes del sistema

```bash
sudo pacman -S python python-pip git postgresql
```

En EndeavourOS, Arch **no inicializa el cluster de PostgreSQL automáticamente**.
Una sola vez, después de instalar:

```bash
sudo postgresql-setup --initialize
sudo systemctl enable --now postgresql
```

Comprobar que responde:

```bash
pg_isready
# debería decir: accepting connections
```

## 1.2 Clonar el proyecto

```bash
git clone git@github.com:segueldev/caracales-web.git
cd caracales-web
```

(Con HTTPS: `git clone https://github.com/segueldev/caracales-web.git`)

## 1.3 Configurar las credenciales

```bash
cp .env.example .env
nano .env        # o vim, gedit, el editor que prefieras
```

Completa al menos `DB_PASSWORD` (la contraseña del **rol de PostgreSQL**, no la
de Django). También puedes cambiar `DB_USER` si no usas `postgres`.

> Consejo: para no tipear la contraseña de PostgreSQL en cada conexión puedes
> crear un archivo `~/.pgpass` con `host:5432:*:postgres:TU_PASSWORD:*`.

## 1.4 Arrancar

```bash
./iniciar.sh
```

El script hace todo: crea `venv/`, instala dependencias, copia `.env` si falta,
verifica PostgreSQL, crea la base de datos si no existe, migra, carga la demo
y levanta el servidor.

## 1.5 Detener

`Ctrl + C` en la terminal.

## 1.6 Manual (si prefieres paso a paso)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py poblar_demo
python manage.py runserver
```

## 1.7 Errores frecuentes en Linux

| Mensaje | Solución |
|---|---|
| `could not connect to server` | `sudo systemctl start postgresql` |
| `password authentication failed` | Revisa `DB_PASSWORD` en `.env` |
| `database academia_felina does not exist` | `createdb academia_felina` (o vuelve a correr `./iniciar.sh`) |
| `Permission denied for table ...` | El `DB_USER` no es dueño de la BD; usa `postgres` o dale permisos |
| `ModuleNotFoundError: psycopg` | `source venv/bin/activate && pip install -r requirements.txt` |
| Puerto 8000 ocupado | `python manage.py runserver 8080` |


# 2. WINDOWS (10 / 11)

## 2.1 Instalar Python

Descarga desde <https://www.python.org/downloads/> y **marca la casilla
"Add python.exe to PATH"** en el primer paso del instalador (es el error más
común). Verifica en una terminal:

```bat
python --version
```

## 2.2 Instalar PostgreSQL

Instalador oficial: <https://www.postgresql.org/download/windows/>.

- Durante la instalación, apunta bien la **contraseña del superusuario postgres**
  (es la que va en `.env`).
- Deja marcada la opción **"Stack Builder"** sólo si quieres: no es necesaria.
- Asegúrate de que el servicio **"postgresql-x64-XX"** esté en *Automático*
  (se hace desde `services.msc` o desde el instalador).

Si `psql` no queda en el PATH, el instalador lo agrega a
`C:\Program Files\PostgreSQL\XX\bin`; `iniciar.bat` lo busca ahí solo.

## 2.3 Clonar y arrancar

```bat
git clone https://github.com/segueldev/caracales-web.git
cd caracales-web
notepad .env       # pon tu contraseña de PostgreSQL
iniciar.bat
```

## 2.4 Errores frecuentes en Windows

| Mensaje | Solución |
|---|---|
| `'python' is not recognized` | Reinstala Python marcando *Add to PATH* y abre una terminal nueva |
| `Windows failed to find 'python'` en el Store | Configuración → Aplicaciones → *App ejecutor de aliases de Python* → Desactivar |
| `password authentication failed` | Revisa `DB_PASSWORD` en `.env` (guardado como UTF-8 sin BOM) |
| `psycopg` no instala | `pip install "psycopg[binary,pool]>=3.2"` (el binario trae las DLLs) |
| Puerto 8000 ocupado | `python manage.py runserver 8080` |


# 3. VISUAL STUDIO CODE

El repositorio trae la configuración lista en `.vscode/`.

## 3.1 Abrir el proyecto

```bash
code .
```

o bien VS Code → *Archivo → Abrir carpeta...* y selecciona `academia_felina`.

## 3.2 Elegir el intérprete (una sola vez)

1. `Ctrl+Shift+P` → escribe **Python: Select Interpreter**.
2. Elige `./venv/bin/python` (Linux) o `.\venv\Scripts\python.exe` (Windows).
3. Si no aparece, la extensión **Python** de Microsoft no está instalada
   (la pestaña de extensiones → instalar "Python" → recargar ventana).

## 3.3 Depurar

`Ctrl+Shift+D` abre *Ejecutar y depurar*. Configuraciones incluidas:

| Configuración | Qué hace |
|---|---|
| **Django: servidor de desarrollo** | Arranca `runserver --noreload` y detiene en los breakpoints |
| **Django: migraciones** | Ejecuta `migrate` |
| **Django: datos de demostración** | Ejecuta `poblar_demo` |
| **Django: shell de Django** | Consola interactiva con el proyecto cargado |
| **Python: ejecutar archivo actual** | Depura el archivo abierto |

Para que un breakpoint funcione en el servidor: pon el punto rojo en la línea,
elige **Django: servidor de desarrollo** y pulsa `F5`. Luego entra al sitio en
`http://127.0.0.1:8000/` y cuando el debugger llegue a esa línea se detiene.

> **¿Por qué `--noreload`?** Django, por defecto, relanza el proceso en un hijo
> cuando detecta cambios. El debugger queda enganchado al padre y "no entra"
> a los breakpoints. `--noreload` desactiva esa doble capa.

## 3.4 Tareas integradas

`Ctrl+Shift+P` → **Tareas: ejecutar tarea...**:

- `Iniciar proyecto` → corre `./iniciar.sh` o `iniciar.bat` según el SO.
- `Django: migraciones`
- `Django: check`

## 3.5 Terminal integrada

VS Code activa el entorno virtual automáticamente
(`python.terminal.activateEnvironment`). Verás `(venv)` al inicio del prompt.
Si no aparece, ejecuta a mano:

- Linux/macOS: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`


# 4. ESTRUCTURA DEL PROYECTO

```
academia_felina/
├── iniciar.sh                  ← arranque automático en Linux/macOS
├── iniciar.bat                 ← arranque automático en Windows
├── manage.py                   ← punto de entrada de Django
├── requirements.txt            ← dependencias congeladas
├── .env.example                ← plantilla de variables de entorno
├── .env                        ← valores reales (NO se sube a Git)
├── README.md                   ← descripción general y checklist de la pauta
├── INSTRUCCIONES.md            ← este archivo
├── .vscode/                    ← debug y tareas de VS Code
│
├── academia_felina/            ← paquete del proyecto (configuración)
│   ├── settings.py             ← PostgreSQL, JWT, DRF, Swagger, datos alumno
│   ├── urls.py                 ← rutas raíz (API + vistas HTML)
│   ├── wsgi.py / asgi.py       ← puntos de entrada del servidor
│
├── apps/                       ← aplicaciones del proyecto
│   ├── core/                   ← modelos base, permisos RBAC, footer, home
│   │   ├── permissions.py      ← IsEstudiante / IsCoordinador / IsOwnerOrCoordinador
│   │   ├── views.py            ← vistas HTML (home, catálogo, historia...)
│   │   └── context_processors.py  ← datos del alumno para el footer
│   ├── usuarios/               ← usuario personalizado con roles
│   │   ├── models.py           ← Usuario con Rol (ESTUDIANTE/COORDINADOR)
│   │   ├── tokens.py           ← CustomAccessToken/RefreshToken (claims rol)
│   │   ├── serializers.py      ← registro, login, refresh, perfil
│   │   └── views.py            ← endpoints JWT
│   ├── academico/              ← catálogo (público)
│   │   ├── models.py           ← AreaConocimiento y Curso (cupos, CHOICES)
│   │   ├── filters.py          ← CursoFilter / AreaFilter (django-filter)
│   │   ├── serializers.py      ← list / detail / coordinador
│   │   └── views.py            ← ViewSets con permisos por acción
│   └── matriculas/             ← carro, órdenes y matrículas
│       ├── models.py           ← CarroMatricula (1:1), OrdenMatricula, MatriculaDetalle
│       ├── services.py         ← checkout atómico: SELECT FOR UPDATE + cupos
│       ├── views.py            ← ViewSets de carro / órdenes / coordinador
│       └── signals.py          ← señales de la sesión
│
├── templates/                  ← plantillas HTML (estilo Liquid Glass)
├── static/                     ← CSS, JS, texturas e iconos
├── media/                      ← imágenes subidas (cursos de demostración)
└── venv/                       ← entorno virtual (no se sube a Git)
```


# 5. CREDENCIALES DE DEMOSTRACIÓN

| Rol | Usuario | Contraseña |
|---|---|---|
| Coordinador Académico | `coordinador` | `coordinador123` |
| Estudiante (x4) | `estudiante1` … `estudiante4` | `floppa123` |

- Sitio web: <http://127.0.0.1:8000/>
- Swagger/OpenAPI: <http://127.0.0.1:8000/api/docs/>
- Admin de Django: <http://127.0.0.1:8000/admin/>


# 6. COMANDOS ÚTILES DE DJANGO

```bash
python manage.py runserver            # servidor de desarrollo
python manage.py migrate              # aplicar migraciones
python manage.py makemigrations       # generar migraciones de cambios
python manage.py poblar_demo          # (re)cargar datos de demostración
python manage.py check                # verificación de configuración
python manage.py shell                # consola interactiva
python manage.py createsuperusuario   # crear usuario de /admin/
python manage.py spectacular --file schema.yaml   # exportar el esquema OpenAPI
```


# 7. BASE DE DATOS

El nombre por defecto es `academia_felina`. Para verla en consola:

```bash
psql -U postgres -d academia_felina
```

```sql
\dt                          -- listar tablas
SELECT username, rol FROM usuarios_usuario;
SELECT id, nombre, cupos_maximos, cupos_disponibles FROM academico_curso;
SELECT numero_orden, estado FROM matriculas_ordenmatricula;
\q                           -- salir
```
