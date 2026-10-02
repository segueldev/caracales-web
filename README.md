# Academia Felina Floppa - EVA 2 Backend

**Proyecto de Evaluación EVA 2 - Unidad 2**  
**Asignatura:** Programación Back End - Desarrollo Backend  
**Alumno:** Benjamín Seguel  
**Carrera:** Ingeniería en Ciberseguridad  
**Sección:** TI3041/IEC-N4-C1/D Temuco IEC  
**Profesor:** Marcelo Patricio Alvarado Aravena  
**Año:** 2026  

---

## Descripción

Backend completo con **Django REST Framework** para la "Academia Felina Floppa" - plataforma de cursos/bootcamps para caracales, adaptada del **Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)** del enunciado.

### Temática
- **Mascota:** Floppa (Caracal caracal) - felino salvaje de África/Asia
- **Diseño:** Liquid Glass / Glassmorphism (heredado del prototipo frontend anterior)
- **Funcionalidad:** Catálogo público, carro de matrícula persistente, checkout transaccional, gestión de cupos

---

## Requisitos Cumplidos (Según Pauta EVA 2)

### ✅ Base de Datos: PostgreSQL (NO SQLite)
- Configuración nativa `django.db.backends.postgresql` en `settings.py`

### ✅ Autenticación JWT con Roles (RBAC)
- **Access + Refresh tokens** con `djangorestframework-simplejwt`
- **Claims personalizados:** `rol` (ESTUDIANTE/COORDINADOR), `username`, `email`, `nombre_completo`
- **Permisos DRF:**
  - Público: GET /api/catalogo/cursos/, /api/catalogo/areas/
  - Estudiante (IsAuthenticated): Carro, Checkout, Mis Órdenes
  - Coordinador (IsAdminUser/Custom): CRUD Cursos, Cambio estados órdenes

### ✅ Modelo de Datos con CHOICES
- `Usuario.rol` - CHOICES explícito (ESTUDIANTE/COORDINADOR)
- `Curso.estado` - CHOICES (BORRADOR/PUBLICADO/ARCHIVADO)
- `Curso.modalidad` - CHOICES (PRESENCIAL/VIRTUAL/HIBRIDO)
- `OrdenMatricula.estado` - CHOICES (PENDIENTE/PAGADO/ENTREGADO/CANCELADO)
- Relaciones FK, OneToOne, ManyToMany con integridad referencial

### ✅ Carro de Compras Persistente (1:1 Usuario-Carro)
- `CarroMatricula` - OneToOne con Usuario (ESTUDIANTE)
- Persiste en PostgreSQL tras logout/cambio de dispositivo
- Signal `post_save` crea carro automáticamente al registrar estudiante
- Items con snapshot de precio/datos al agregar (no descuenta cupos)

### ✅ Transacciones, Stock/Cupos y Estados
- **Checkout:** Crea `OrdenMatricula` PENDIENTE, vacía carro, crea `MatriculaDetalle` inactivas
- **Pago (PENDIENTE → PAGADO):** 
  - `SELECT FOR UPDATE` bloquea cursos
  - Valida cupos disponibles **atómicamente**
  - Si hay cupo: descuenta `cupos_disponibles`, activa matrículas, marca PAGADO
  - Si NO hay cupo: **ROLLBACK total**, rechaza transacción
- **Cancelación (PAGADO → CANCELADO):** Libera cupos automáticamente (`liberar_cupo()`)
- **Entrega (PAGADO → ENTREGADO):** Marca completado

### ✅ Filtros y Búsqueda (django-filter)
- `CursoFilter`: área, modalidad, estado, rango precios, rango fechas, disponibles, búsqueda texto
- `AreaFilter`: activa, búsqueda texto
- Integrado en ViewSets con `DjangoFilterBackend`

### ✅ Documentación API Swagger/OpenAPI
- `drf-spectacular` configurado
- Endpoints: `/api/schema/`, `/api/docs/` (Swagger UI), `/api/redoc/`
- Tags organizados: Autenticación, Catálogo, Carro, Matrículas

### ✅ Código Documentado en Bloques
- Todos los modelos, vistas, serializers, services, permissions, signals con docstrings explicativos
- Comentarios inline en lógica compleja (transacciones, signals, validaciones)

### ✅ Footer con Datos Alumno
- Context processor `datos_alumno` inyecta en **todos los templates**
- Visible en base.html: Nombre, Carrera, Sección, Evaluación, Profesor, Institución, Año

---

## Stack Tecnológico

- **Python:** 3.10+ (probado en **3.14.7**)
- **Django:** 5.2.17 (rama **LTS**)
- **Django REST Framework:** 3.15.2
- **Simple JWT:** 5.3.1 (tokens + blacklist + rotación)
- **django-filter:** 23.5
- **drf-spectacular:** 0.27.2 (OpenAPI 3)
- **PostgreSQL:** 14+ (driver **psycopg 3** — `psycopg[binary,pool]`)
- **Pillow:** 11+ (subida de imágenes de cursos/áreas)
- **Frontend:** Bootstrap 5, DataTables, jQuery, Liquid Glass CSS custom

---

## Inicio rápido

El proyecto incluye scripts de arranque automáticos para no tener que tipear
comandos sueltos:

| SO | Comando |
|---|---|
| Linux / macOS | `./iniciar.sh` |
| Windows | doble clic en `iniciar.bat` |
| VS Code | `Ctrl+Shift+P` → *Tareas: ejecutar tarea...* → **Iniciar proyecto** |

El script crea `venv/`, instala dependencias, copia `.env.example` a `.env`,
comprueba que PostgreSQL esté corriendo, crea la base de datos si no existe,
aplica migraciones, carga los datos de demostración **sólo si la tabla está
vacía** y finalmente levanta el servidor.

> La guía completa —con los pasos manuales, los errores frecuentes de cada SO
> y la configuración de depuración de VS Code— está en **[INSTRUCCIONES.md](INSTRUCCIONES.md)**.

Verificación de salud del proyecto (última corrida):

```
Regresión de URLs   : 109 rutas × 3 roles = 207 peticiones, 0 respuestas 5xx
Flujo E2E completo  : 37/37 comprobaciones OK
                      (JWT + claims, carro 1:1, confirmar, pagar, cupos
                       20 → 19, cancelar → 20, rutas alias de la pauta)
Django check        : 0 issues
/api/docs/ y /api/schema/ : 200
```

---

## Estructura del Proyecto

```
academia_felina/
├── iniciar.sh                  # Arranque automático en Linux/macOS
├── iniciar.bat                 # Arranque automático en Windows
├── INSTRUCCIONES.md            # Guía de instalación Linux/Windows/VS Code
├── academia_felina/            # Configuración principal (settings, urls, wsgi, asgi)
├── .vscode/                    # Depuración y tareas de VS Code
├── apps/
│   ├── core/                 # Modelos base, permisos, context_processors, vistas HTML
│   ├── usuarios/             # Usuario personalizado, JWT tokens, auth API + templates
│   ├── academico/            # AreaConocimiento, Curso, catálogo público + filtros
│   └── matriculas/           # CarroMatricula, ItemCarro, OrdenMatricula, MatriculaDetalle
├── templates/                # Templates Django (base.html, core/, registration/)
├── static/                   # CSS, JS, assets (imágenes, audio del prototipo)
├── media/                    # Uploads (avatares, imágenes cursos)
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Instalación y Ejecución

> **Atajo:** en Linux ejecuta `./iniciar.sh` y en Windows `iniciar.bat`.
> Lo que sigue es el procedimiento manual equivalente.

### 1. Clonar y entrar al directorio
```bash
git clone git@github.com:segueldev/caracales-web.git
cd caracales-web
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales PostgreSQL reales
```

**Variables requeridas en `.env`:**
```env
SECRET_KEY=tu-secret-key-generada-con-django-secret-key-generator
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=academia_felina
DB_USER=postgres
DB_PASSWORD=tu-password-postgres
DB_HOST=localhost
DB_PORT=5432

JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
```

### 4. Crear base de datos PostgreSQL
```sql
-- En psql o pgAdmin
CREATE DATABASE academia_felina;
CREATE USER postgres WITH PASSWORD 'tu-password';
GRANT ALL PRIVILEGES ON DATABASE academia_felina TO postgres;
```

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario (coordinador)
```bash
python manage.py createsuperuser
# Usuario: coordinador
# Email: coordinador@floppa.cl
# Password: **********
# Luego editar en admin: rol = COORDINADOR
```

### 7. Cargar datos de prueba (recomendado para la defensa)

En lugar de escribir registros a mano existe un **comando propio** que puebla la
base de forma **idempotente** (se puede ejecutar tantas veces como se quiera sin
duplicar nada):

```bash
python manage.py poblar_demo
```

Qué crea:

| Datos | Cantidad | Detalle |
|-------|----------|---------|
| Áreas de conocimiento | 5 | Caza, Sigilo, Ronroneo, Trepar, Historia Felina |
| Cursos `PUBLICADO` | 8 | Códigos FLF-001 … FLF-008 (FLF-008 agotado con **0 cupos**) |
| Estudiantes | 4 | rol `ESTUDIANTE`, generan el conteo de estadísticas |
| Coordinador | 1 | rol `COORDINADOR` |

> El comando está documentado en bloques en
> `apps/core/management/commands/poblar_demo.py`.

#### Cuentas de prueba

| Usuario | Clave | Rol | Qué permite ver |
|---------|-------|-----|-----------------|
| `estudiante1` … `estudiante4` | `floppa123` | ESTUDIANTE | Carro persistente, checkout, pagar/cancelar, Mis Matrículas |
| `coordinador` | `coordinador123` | COORDINADOR | Panel Coordinador, CRUD cursos/áreas, gestión de órdenes |

> ⚠️ Son credenciales de demostración: cámbialas antes de publicar el proyecto.

### 8. Ejecutar servidor
```bash
python manage.py runserver
```

### 9. Acceder
- **Web App:** http://localhost:8000/
- **Admin Django:** http://localhost:8000/admin/
- **Swagger API:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Health Check:** http://localhost:8000/health/

---

## Iconos personalizados (carpeta para subir imágenes)

Los iconos del home se muestran como **emoji de respaldo**. Para reemplazarlos
con imágenes propias basta con subir el archivo con el nombre exacto a
`static/assets/iconos/`; **no hay que tocar código ni reiniciar nada**.

```
static/assets/iconos/
├── README.md                 ← tabla completa de nombres y especificaciones
├── estadisticas/             ← tarjetas de estadísticas del home
│   ├── cursos.png               (respaldo 📚)
│   ├── areas.png                (respaldo 🎯)
│   └── estudiantes.png          (respaldo 🐱)
├── caracteristicas/          ← tarjetas "¿Por qué elegirnos?"
│   ├── instructores.png         (respaldo 🏆)
│   ├── metodologia.png          (respaldo ⚔️)
│   ├── certificacion.png        (respaldo 📜)
│   └── comunidad.png            (respaldo 👥)
└── areas/                    ← portada de cada área en las tarjetas de cursos
    ├── caza.png, sigilo.png, ronroneo.png, trepar.png, historia-felina.png
```

**Especificaciones recomendadas:** PNG cuadrado con transparencia, 256×256 px,
menos de 100 KB.

El mecanismo usa un **template tag propio** (`{% static_exists %}` en
`apps/core/templatetags/estilos_extras.py`) que consulta los *static finders*
de Django y decide entre la imagen o el emoji:

```django
{% load estilos_extras %}
{% static_exists 'assets/iconos/estadisticas/cursos.png' as hay_icono %}
{% if hay_icono %}<img src="...">{% else %}<span>📚</span>{% endif %}
```

---

## Assets entregados por el usuario

Todos los archivos siguientes provienen de la carpeta de entrega del alumno y
fueron copiados a `static/assets/`. Ningún ícono fue generado por IA.

| Archivo | Dónde se usa |
|---|---|
| `textura-floppa.jpg` | fondo de botones e insignias de sección |
| `textura-madera.jpg` | fondo de las tarjetas "¿Por qué elegirnos?" |
| `textura-papel.jpg` | fondo de las tarjetas de estadística |
| `textura-piedra-laja.jpg`, `textura-footer.jpg` | fondo del pie de página |
| `textura-matricula.jpg` | **insignia de cupos** (es un pizarrón: entra el marco de madera) |
| `textura-cesped.webp` | botón "Ver todo el catálogo" (`.btn-cesped`) |
| `textura-caracal.webp` | **borde** de los botones `.btn-outline-floppa` (reemplaza al naranja neón) |
| `iconos/punto-floppa.png` | punto de la insignia del hero |
| `iconos/flecha-roja.png` | flecha del botón de catálogo |
| `iconos/certificado.png`, `vitalicia.png`, `privada.png` | indicadores de confianza del hero |
| `iconos/cupo.png` | ticket que sobresale de la insignia de cupos |
| `iconos/comprobado.png` | sello *FEATURED* junto a "Destacados" |
| `iconos/sombrero.png` | birrete a la derecha de "Matrícula Abierta 2026" |
| `iconos/meganoticias.png` | sello de prensa en `/nuestra-historia/` |
| `iconos/peso-chileno.png` | billete del formato de precio `CLP 499.990` |
| `iconos/areas/caza.png` | **hacha** del área Caza (API: `area_icono_img`) |
| `historia-esfinge.jpg` | imagen del manifiesto `/nuestra-historia/` |
| `sello-plagio.webp` | sello "Plágio é crime" junto a la firma (recortado de 6 MB a 106 KB) |

## Interacciones del frontend

- **Formato de precio chileno**: `CLP 499.990` + billete, en catálogo, home,
  carro, mis matrículas y panel del coordinador (`AcademiaFloppa.precioHTML`).
- **Modal de detalle de curso**: al hacer clic en una tarjeta se consulta
  `GET /api/catalogo/cursos/<id>/` y se abre el modal de Bootstrap.
- **Dato curioso**: las tarjetas de "¿Por qué elegirnos?" son clicables
  (también con `Enter`/`Espacio`) y muestran un dato de los caracales con
  animación de giro. Los textos salen de `features[].dato` en `HomeView`.
- **Banda "Nuestra historia y nuestra lucha contra el plagio"**: titular
  enorme en tipografía *Alfa Slab One* que enlaza a `/nuestra-historia/`.
- **`/nuestra-historia/`**: manifiesto de origen; al pasar el mouse por el
  titular, "Ducommun Marcelo" se subraya en rojo.
- **Contorno del texto con degradado**: el trazo crema se pinta en un
  `::before` con `z-index: -1`. No puede ir en el propio elemento porque
  `-webkit-text-stroke` se pinta *después* del `background-clip: text` y
  tapaba el degradado (el texto salía borroso).

---

## Endpoints API Principales

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/registro/` | Registro estudiante (retorna tokens) |
| POST | `/api/auth/login/` | Login username/email + password |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET/PATCH | `/api/auth/perfil/` | Perfil usuario autenticado |
| POST | `/api/auth/cambio-password/` | Cambio contraseña |
| POST | `/api/auth/logout/` | Blacklist refresh token |

### Catálogo Público (Sin auth)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/catalogo/areas/` | Listar áreas |
| GET | `/api/catalogo/areas/{id}/` | Detalle área + cursos |
| GET | `/api/catalogo/cursos/` | Listar cursos (filtros: area, modalidad, precio_min/max, fecha_inicio_desde/hasta, disponible, search) |
| GET | `/api/catalogo/cursos/{id}/` | Detalle curso |
| GET | `/api/catalogo/cursos/{id}/disponibilidad/` | Cupos en tiempo real |

### Carro de Matrícula (Estudiante - JWT)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/carro/` | Ver carro (items, totales) |
| POST | `/api/carro/agregar/` | Agregar curso `{curso_id}` |
| DELETE | `/api/carro/quitar/{curso_id}/` | Quitar curso |
| DELETE | `/api/carro/limpiar/` | Vaciar carro |
| POST | `/api/carro/checkout/` | Crear orden PENDIENTE |

### Mis Órdenes (Estudiante - JWT)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/matriculas/mis-ordenes/` | Listar mis órdenes |
| GET | `/api/matriculas/mis-ordenes/{id}/` | Detalle orden + matrículas |
| POST | `/api/matriculas/mis-ordenes/{id}/pagar/` | Pagar orden (PENDIENTE→PAGADO) |
| POST | `/api/matriculas/mis-ordenes/{id}/cancelar/` | Cancelar orden (libera cupos si pagada) |

### Gestión Coordinador (JWT + Rol COORDINADOR)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/POST | `/api/catalogo/cursos/` | CRUD cursos |
| GET/POST | `/api/catalogo/areas/` | CRUD áreas |
| GET | `/api/matriculas/gestion/` | Listar todas las órdenes |
| PATCH | `/api/matriculas/gestion/{id}/estado/` | Cambiar estado (PAGADO→ENTREGADO/CANCELADO) |

### Rutas exactas de la MATRIZ DE PERMISOS de la pauta (Proyecto 2)

La pauta EVA 2 enumera textualmente estas rutas. Son **alias**: no repiten
lógica, apuntan a la misma vista/acción que las tablas anteriores. Esto hace
que la matriz de la pauta se pueda demostrar tal cual está escrita:

| Rol | Ruta (según pauta) | Implementación |
|-----|--------------------|----------------|
| PÚBLICO | `GET /api/cursos/` | `GET /api/catalogo/cursos/` |
| PÚBLICO | `GET /api/areas/` | `GET /api/catalogo/areas/` |
| ESTUDIANTE | `GET/POST/DELETE /api/carro-matricula/` | `GET/POST/DELETE /api/carro/` |
| ESTUDIANTE | `POST /api/matriculas/confirmar/` | alias de `POST /api/carro/checkout/` |
| ESTUDIANTE | `GET /api/mis-matriculas/` | alias de `GET /api/matriculas/mis-ordenes/` |
| ESTUDIANTE | `GET /api/mis-matriculas/{id}/` | alias del detalle |
| ESTUDIANTE | `POST /api/mis-matriculas/{id}/pagar/` | alias de `.../mis-ordenes/{id}/pagar/` |
| ESTUDIANTE | `POST /api/mis-matriculas/{id}/cancelar/` | alias de `.../mis-ordenes/{id}/cancelar/` |
| COORDINADOR | `POST/PUT/DELETE /api/cursos/` | `POST/PUT/DELETE /api/catalogo/cursos/` (403 si no es coordinador) |
| COORDINADOR | `PATCH /api/matriculas/{id}/estado/` | alias de `PATCH /api/matriculas/gestion/{id}/estado/` |

---

## Flujo de Matrícula (Para Defensa Oral)

1. **Estudiante navega catálogo público** → GET `/api/catalogo/cursos/`
2. **Agrega cursos al carro** → POST `/api/carro/agregar/` (valida cupos, NO descuenta)
3. **Carro persiste** en PostgreSQL (1:1 User-Carro) tras logout/login
4. **Checkout** → POST `/api/carro/checkout/` → Crea `OrdenMatricula` PENDIENTE, vacía carro
5. **Pago** → POST `/api/matriculas/mis-ordenes/{id}/pagar/`
   - Transacción atómica: `SELECT FOR UPDATE` en cursos
   - Valida `cupos_disponibles > 0` para TODOS los items
   - Si OK: `descontar_cupo()` each, activa `MatriculaDetalle`, estado → PAGADO
   - Si FAIL: ROLLBACK, error "cupos insuficientes"
6. **Coordinador ve órdenes** → GET `/api/matriculas/gestion/`
7. **Cambio estado** → PATCH `/api/matriculas/gestion/{id}/estado/`
   - PAGADO → ENTREGADO (curso finalizado)
   - PAGADO → CANCELADO (libera cupos con `liberar_cupo()`)

---

## Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Superusuario
python manage.py createsuperuser

# Datos de demostración (idempotente)
python manage.py poblar_demo

# Shell interactivo
python manage.py shell

# Collect static (producción)
python manage.py collectstatic

# Documentación OpenAPI (genera el esquema en disco)
python manage.py spectacular --file schema.yml

# Tests
python manage.py test

# Verificar migraciones pendientes
python manage.py showmigrations
```

---

## Publicación en GitHub (Requerido por Pauta)

### 1. Crear el repositorio

Entrar a <https://github.com/new> y crear un repositorio **academia_felina**
(público o privado, lo que prefieras) **sin** inicializarlo con README ni
`.gitignore` (ya vienen incluidos en el proyecto).

### 2. Ejecutar los comandos en este orden

```bash
cd academia_felina

git init
git branch -M main

# Revisa qué se va a subir (no debe aparecer venv/ ni .env)
git status

git add .
git commit -m "EVA 2 Backend - Academia Felina Floppa - Django REST Framework + PostgreSQL + JWT + Liquid Glass"

git remote add origin git@github.com:segueldev/caracales-web.git
git push -u origin main
```

> **Repositorio del proyecto:** <https://github.com/segueldev/caracales-web>
> Rama `main`, autenticación por **SSH**.

### 3. Autenticación (ya configurada en este proyecto)

GitHub **no acepta la contraseña de la cuenta** para hacer `git push`. Este
proyecto quedó configurado con **SSH**, que es la opción recomendada:

```bash
# Clave generada (una sola vez)
ssh-keygen -t ed25519 -C "tu_email@ejemplo.com"
cat ~/.ssh/id_ed25519.pub      # copiar el resultado

# Registrarla en GitHub: https://github.com/settings/keys → "New SSH key"
# Verificar (debe responder "Hi <usuario>!")
ssh -T git@github.com
```

Comprobación hecha en este proyecto:

```text
Hi segueldev! You've successfully authenticated, but GitHub does not provide shell access.
```

**Alternativa — Token de acceso personal (HTTPS)**, si se necesita desde otra
máquina:

1. Ir a <https://github.com/settings/tokens/new>
2. Marcar el permiso **`repo`**
3. Copiar el token (`ghp_...`)
4. Al hacer `git push`: *Username* = usuario de GitHub, *Password* = **el token**

```bash
git config --global credential.helper store   # lo recuerda la próxima vez
```

### 4. Verificar

Después del push, abrir el repositorio y comprobar que aparecen:
`academia_felina/`, `apps/`, `templates/`, `static/`, `README.md`.
**No** deben aparecer `venv/`, `.env` ni `staticfiles/` (están en `.gitignore`).

> **¡IMPORTANTE!** El proyecto debe estar en GitHub antes de la hora límite de
> entrega. Cada modificación posterior se sube con:
>
> ```bash
> git add .
> git commit -m "Descripción del cambio"
> git push
> ```

---

## Créditos

- **Diseño Liquid Glass:** Adaptado del prototipo "Club Felino Floppa" (Evaluación Front End anterior)
- **Assets:** Imágenes y audio del prototipo original (caracales, burbujas, sonidos de vidrio/agua)
- **Temática:** Floppa (Caracal caracal) - meme felino de internet

---

## Licencia

Proyecto académico para Evaluación EVA 2 - INACAP Temuco 2026. Uso educativo únicamente.