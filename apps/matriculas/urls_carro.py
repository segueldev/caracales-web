"""
=============================================================================
URLS DEL CARRO DE MATRÍCULA — se montan EXCLUSIVAMENTE en /api/carro/
=============================================================================
Por qué existe este archivo:

    apps/matriculas/urls.py se incluye en DOS prefijos del proyecto
    (/api/carro/ y /api/matriculas/) y ahí las rutas del carro llevan un
    prefijo extra "carro/". Montado en /api/carro/ eso generaba rutas dobles
    (/api/carro/carro/agregar/) y por lo tanto devolvía 404 a las llamadas
    reales que hacen los templates (home, catálogo y mi carro).

    Aquí las rutas se declaran ya SIN ese prefijo, de modo que quedan
    exactamente las URLs documentadas en CarroMatriculaViewSet:

        GET    /api/carro/                    -> ver carro (items y totales)
        POST   /api/carro/agregar/            -> agregar un curso al carro
        DELETE /api/carro/quitar/<curso_id>/  -> quitar un curso del carro
        DELETE /api/carro/limpiar/            -> vaciar el carro completo
        POST   /api/carro/checkout/           -> crear la orden PENDIENTE

    /api/matriculas/ sigue sirviendo el resto de endpoints (órdenes,
    pagos, gestión del coordinador) a través de apps/matriculas/urls.py.
=============================================================================
"""
from django.urls import path

from apps.matriculas.views import CarroMatriculaViewSet

urlpatterns = [
    # GET /api/carro/  -> carro persistente 1:1 del estudiante autenticado
    path(
        '',
        CarroMatriculaViewSet.as_view({'get': 'retrieve'}),
        name='api-carro-detalle',
    ),
    # POST /api/carro/agregar/  -> body: {"curso_id": <id>}
    path(
        'agregar/',
        CarroMatriculaViewSet.as_view({'post': 'agregar'}),
        name='api-carro-agregar',
    ),
    # DELETE /api/carro/quitar/<curso_id>/
    path(
        'quitar/<int:curso_id>/',
        CarroMatriculaViewSet.as_view({'delete': 'quitar'}),
        name='api-carro-quitar',
    ),
    # DELETE /api/carro/limpiar/
    path(
        'limpiar/',
        CarroMatriculaViewSet.as_view({'delete': 'limpiar'}),
        name='api-carro-limpiar',
    ),
    # POST /api/carro/checkout/ -> bloqueo transaccional de cupos + stock
    path(
        'checkout/',
        CarroMatriculaViewSet.as_view({'post': 'checkout'}),
        name='api-carro-checkout',
    ),
]
