# 🖼️ Iconos de la Academia Felina Floppa

Aquí se suben las **imágenes que reemplazan a los emojis** de la página de inicio.

> Mientras un archivo **no exista**, la web muestra el emoji de respaldo.
> En cuanto coloques la imagen con el nombre exacto, aparece sola (sin tocar código).

---

## 📁 Estructura y nombres exactos

### `estadisticas/` → tarjetas de la sección de estadísticas

| Archivo | Emoji de respaldo | Dónde se ve |
|---|---|---|
| `estadisticas/cursos.png` | 📚 | "Cursos Disponibles" |
| `estadisticas/areas.png` | 🎯 | "Áreas de Conocimiento" |
| `estadisticas/estudiantes.png` | 🐱 | "Estudiantes Inscritos" |

### `caracteristicas/` → tarjetas "¿Por qué elegirnos?"

| Archivo | Emoji de respaldo |
|---|---|
| `caracteristicas/instructores.png` | 🏆 |
| `caracteristicas/metodologia.png` | ⚔️ |
| `caracteristicas/certificacion.png` | 📜 |
| `caracteristicas/comunidad.png` | 👥 |

### `areas/` → imagen de portada de cada área en las tarjetas de cursos

| Archivo | Emoji de respaldo | Área |
|---|---|---|
| `areas/caza.png` | 🎯 | Caza |
| `areas/sigilo.png` | 🥷 | Sigilo |
| `areas/ronroneo.png` | 🎵 | Ronroneo |
| `areas/trepar.png` | 🧗 | Trepar |
| `areas/historia-felina.png` | 📜 | Historia Felina |

> Los nombres de `areas/` son el **slug** del área (minúsculas, sin tildes,
> guiones en vez de espacios), igual que aparece en la URL del catálogo.

---

## ⚙️ Especificaciones recomendadas

- **Formato:** PNG con fondo transparente (también funciona SVG, WebP o JPG)
- **Tamaño:** cuadrado, **256 × 256 px** (o 512 × 512 px)
- **Peso:** intenta que cada archivo quede **bajo 100 KB**
- **Estilo:** idealmente coherente con la paleta ámbar/dorada del proyecto

## ✔️ Pasos

1. Prepara tu imagen (ej. `mis-iconos/cursos.png`)
2. Renómbrala con el nombre exacto de la tabla
3. Cópiala dentro de la carpeta correspondiente
4. Recarga la página (`Ctrl + Shift + R`)

Si Django está corriendo con `runserver`, **no hay que reiniciar nada**:
los estáticos se sirven desde `static/` en desarrollo.

> Si en algún momento ejecutas `python manage.py collectstatic`,
> vuelve a copiar los archivos a `staticfiles/assets/iconos/`
> (o repite el `collectstatic`) para que también estén en producción.
