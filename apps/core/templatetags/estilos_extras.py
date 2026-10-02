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
