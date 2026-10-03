"""
=============================================================================
CÓDIGOS DE BARRA DEL CATÁLOGO - ACADEMIA FELINA FLOPPA
=============================================================================

Qué hace
--------
Convierte un código de curso (por ejemplo ``FLF-007``) en una imagen SVG de
código de barras lineal, que el catálogo muestra debajo del código en texto.

Por qué existe este módulo
--------------------------
El cliente pidió que "cualquier cadena, como FLF-007, se convierta en código
de barras". Se usa la librería **python-barcode**, que es la recomendada para
Django: genera el código en memoria y devuelve texto, sin escribir archivos en
disco ni necesitar servicios externos.

Decisiones técnicas y por qué
-----------------------------
1) **Formato SVG, no PNG.**
   - Es vectorial: se ve nítido en la tabla, en un proyector o impreso.
   - Pesa ~5 KB por código (un PNG equivalente, ~15 KB) y se cachea igual.
   - No exige Pillow (que sí haría falta con ``ImageWriter``), así que la
     dependencia del proyecto se mantiene mínima.

2) **Symbología Code 39.**
   - Acepta letras mayúsculas, dígitos y ``- . $ / + %`` y espacio, que es
     exactamente la forma de los códigos del catálogo (``FLF-001``).
   - Lleva marca de inicio/parada propia y chequeo de paridad incorporado, así
     que no hace falta calcular dígito verificador.
   - Es el estándar clásico de logística/inventario: cualquiera que vea la
     etiqueta reconoce de qué se trata.

3) **``write_text=False``.**
   - La librería puede imprimir el texto debajo de las barras, pero en la
     tabla el código ya está escrito arriba (``FLF-007``). Duplicarlo sólo
     ensucia la celda, así que se desactiva y el texto accesible va en el
     atributo ``alt`` de la imagen.

4) **Validación obligatoria ANTES de generar.**
   - Code 39 sólo conoce ciertos símbolos. Si llega un carácter fuera del
     juego (``Ñ``, ``á``, un emoji…), python-barcode lanza un ``KeyError``
     crudo y eso se convertiría en un **500** con carita de error en vez de un
     404 limpio. Por eso el patrón se revisa antes.

5) **Público y cacheado.**
   - Un código de barras no revela nada que el catálogo público ya no muestre
     (el código del curso está en la tabla), por lo que la ruta no pide
     sesión. Se sirve con ``Cache-Control`` para que cada redibujado del
     DataTable no regenere la imagen.
=============================================================================
"""
import re

import barcode
from barcode.writer import SVGWriter

# Símbolos admitidos por Code 39 (además de los ya cubiertos: A-Z, 0-9).
# Se valida el texto completo contra este patrón antes de tocar la librería.
PATRON_CODE39 = re.compile(r'^[0-9A-Z\-. $/+%]+$')

# Opciones del escritor. Unidades en milímetros, como las maneja python-barcode:
#   module_width -> ancho de cada barra/espacio
#   bar_height   -> alto de las barras (define la relación de aspecto)
#   quiet_zone   -> margen blanco de seguridad, obligatorio para que un
#                   lector óptico pueda "aislar" el código
OPCIONES_ESCRITOR = {
    'write_text': False,        # el código ya va escrito arriba en la celda
    'module_width': 0.25,       # mm por módulo
    'bar_height': 6,            # mm -> SVG de 52.75 x 17 mm (relación 3.1:1)
    'quiet_zone': 6.5,          # mm de margen blanco a cada lado
    'background': '#ffffff',
    'foreground': '#101418',    # casi negro, mejor contraste que el negro puro
}


def es_codigo_valido(codigo: str) -> bool:
    """
    Indica si el texto se puede codificar como Code 39.

    Se expone aparte para que la vista pueda responder 404 con un mensaje
    claro en lugar de dejar que la librería estalle con un ``KeyError``.
    """
    return bool(codigo) and bool(PATRON_CODE39.match(codigo))


def svg_codigo_barras(codigo: str) -> str:
    """
    Genera el código de barras SVG de un código de curso.

    Parámetros
    ----------
    codigo : str
        Cadena a codificar. Debe pasar :func:`es_codigo_valido` antes.

    Retorna
    -------
    str
        Documento SVG completo (texto, no bytes), listo para devolverse tal
        cual en una respuesta ``image/svg+xml``.

    Lanza
    ------
    ValueError
        Si el código contiene símbolos que Code 39 no conoce. La vista los
        traduce a un 404; esta función no traga errores a propósito para que
        un error de programación no pase inadvertido.
    """
    if not es_codigo_valido(codigo):
        raise ValueError(
            f'El código {codigo!r} contiene caracteres fuera del juego Code 39'
        )

    # OJO: barcode.get() espera una INSTANCIA de escritor, no la clase.
    # Pasar `writer=SVGWriter` (sin parentesis) compila pero revienta después
    # con "set_options() missing 1 required positional argument".
    generador = barcode.get('code39', codigo, writer=SVGWriter())
    svg = generador.render(OPCIONES_ESCRITOR)

    # SVGWriter devuelve bytes en algunas versiones y str en otras.
    if isinstance(svg, bytes):
        svg = svg.decode('utf-8')

    return _añadir_view_box(svg)


def _añadir_view_box(svg: str) -> str:
    """
    Inserta el ``viewBox`` que python-barcode no genera.

    **Por qué hace falta.** Sin ``viewBox``, el SVG no sabe cómo escalar su
    contenido: si la hoja de estilo le pide ``width: 92px`` a la imagen, el
    navegador cambia el lienzo pero dibuja las barras en las mismas
    coordenadas de siempre y el código queda recortado.

    **La trampa de las unidades.** python-barcode escribe cada barra con
    coordenadas absolutas en milímetros (``x="6.500mm"``, ``width="0.250mm"``),
    no en unidades de usuario. Escribir a ciegas

        viewBox="0 0 52.750 17.000"        <- mal

    haría que ese ``6.500mm`` se resolviera a ~24 unidades de usuario dentro
    de un lienzo que sólo mide 52.75: las barras se desplazarían hacia la
    derecha y se aplastarían contra el borde. (Se detectó comparando el SVG
    contra lo que se veía en pantalla.)

    Como sin ``viewBox`` 1 unidad de usuario = 1 px, la conversión correcta es

        viewBox = medidas en mm  x  96 / 25.4      <- bien

    lo que da un lienzo de ~199 x 64 unidades y hace que ``6.500mm`` (=24.57
    px) caiga exactamente donde debe.
    """
    if 'viewBox' in svg:
        return svg

    ancho_mm = re.search(r'width="([\d.]+)mm"', svg)
    alto_mm = re.search(r'height="([\d.]+)mm"', svg)
    if not ancho_mm or not alto_mm:
        return svg  # formato inesperado: se devuelve tal cual, sin reventar

    MM_A_PX = 96.0 / 25.4  # 1 milímetro a 96 dpi = 3.7795… px
    ancho_px = float(ancho_mm.group(1)) * MM_A_PX
    alto_px = float(alto_mm.group(1)) * MM_A_PX

    return svg.replace(
        '<svg ',
        f'<svg viewBox="0 0 {ancho_px:.4f} {alto_px:.4f}" '
        'preserveAspectRatio="xMinYMid meet" ',
        1,
    )
