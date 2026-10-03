"""
Paginación del API.

Por qué existe este módulo
--------------------------
DRF traía `PageNumberPagination` a secas, que sólo acepta `?page=N` y devuelve
siempre la misma cantidad de filas (PAGE_SIZE). Eso alcanza para una lista
cualquiera, pero NO para un DataTable en modo servidor:

    DataTables pide  `?start=10&length=10`  -> quiere las filas 11 a 20.
    Con el paginador de DRF eso se ignoraba y volvían SIEMPRE las 20
    primeras, así que al pasar a la página 2 el usuario veía otra vez la
    página 1 (filas repetidas y las últimas inalcanzables).

Al habilitar `page_size_query_param`, el front puede traducir
`start/length` a `page/page_size` y la paginación queda honesta: lo que
anuncia la barra inferior es exactamente lo que entrega el servidor.

Límites
-------
`max_page_size` evita que un cliente pida 10 000 registros de un tirón:
es el típico punto donde un catálogo público se convierte en una forma
barata de vaciar la base de datos.
"""
from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    """
    Paginador por página que además acepta el tamaño solicitado.

    Parámetros que entiende:

        ?page=2            página que se quiere (1-based)
        ?page_size=50      cuántos ítems por página (opcional)

    Si el cliente no pide nada, cae en PAGE_SIZE (20) definido en settings.
    Si pide más de `max_page_size`, se recorta a ese tope en vez de fallar.
    """

    page_size = 20                    # valor por defecto (igual que PAGE_SIZE)
    page_size_query_param = 'page_size'  # habilita ?page_size=
    max_page_size = 100               # techo duro por petición
