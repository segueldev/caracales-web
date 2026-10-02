"""
=============================================================================
TEMPLATE TAGS - ACADEMIA FELINA FLOPPA
=============================================================================
Etiquetas auxiliares para los templates del proyecto.
=============================================================================
"""
from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.simple_tag
def static_exists(ruta_relativa):
    """
    Devuelve True si existe un archivo dentro de static/.

    Uso en el template:

        {% load estilos_extras %}
        {% static_exists 'assets/iconos/estadisticas/cursos.png' as hay_imagen %}
        {% if hay_imagen %}
            <img src="{% static 'assets/iconos/estadisticas/cursos.png' %}" alt="">
        {% else %}
            <span>📚</span>          {# emoji de respaldo #}
        {% endif %}

    Motivo: así la página se ve completa aunque todavía no se hayan subido
    las imágenes de iconos. En cuanto se coloca el archivo con el nombre
    indicado (ver static/assets/iconos/README.md) pasa a mostrarse la imagen.
    """
    if not ruta_relativa:
        return False
    # finders.search en los directorios de origen (STATICFILES_DIRS + apps),
    # que es exactamente lo que usa Django para servir los estáticos en dev.
    return finders.find(ruta_relativa) is not None


@register.filter(name='clp')
def clp(valor):
    """
    Formatea un precio en pesos chilenos con separador de miles (punto).

    Uso en el template:

        {% load estilos_extras %}
        CLP {{ curso.precio|clp }}     {# 499990 -> 499.990 #}
        CLP {{ curso.precio|clp }}     {#  79990 ->  79.990 #}

    Motivo: `floatformat:0` no agrupa los miles y el precio se leía como
    "499990". Se hace el formateo en Python para que la vista HTML coincida
    exactamente con lo que muestra el JavaScript (toLocaleString('es-CL')).
    """
    try:
        return f"{int(round(float(valor))):,}".replace(',', '.')
    except (TypeError, ValueError):
        return valor
