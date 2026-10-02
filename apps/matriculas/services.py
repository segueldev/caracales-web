"""
=============================================================================
SERVICIOS TRANSACCIONALES - ACADEMIA FELINA FLOPPA
=============================================================================
Lógica de negocio compleja para checkout, pago, cancelación.
Manejo atómico de cupos (SELECT FOR UPDATE, transacciones).
=============================================================================
"""
from django.db import transaction
from django.utils import timezone
from apps.matriculas.models import OrdenMatricula, MatriculaDetalle
from apps.academico.models import Curso


@transaction.atomic
def procesar_pago_orden(orden: OrdenMatricula, metodo_pago: str = 'simulado') -> OrdenMatricula:
    """
    Procesa el pago de una orden PENDIENTE -> PAGADO.
    
    FLUJO ATÓMICO (REQUERIDO POR PAUTA):
    1. Bloquea cursos con SELECT FOR UPDATE
    2. Valida cupos disponibles para CADA curso
    3. Si TODOS tienen cupo: descuenta cupos, crea MatriculaDetalle, marca PAGADO
    4. Si ALGUNO no tiene cupo: ROLLBACK completo, rechaza transacción
    
    CUMPLE PAUTA:
    - "Descuento de Inventario: El stock o cupo NO se descuenta al agregar al carro,
      sino en el momento exacto en que la transacción se valida como PAGADO"
    - "Manejo de Stock: Si el stock es insuficiente al pagar, la transacción se rechaza"
    """
    # --- PUNTO DE CONTROL 1: la orden debe estar PENDIENTE -----------------
    # Se descuenta cupo SÓLO al pasar a PAGADO (pauta D). Si la orden ya está
    # PAGADA/ENTREGADA/CANCELADA, volver a pagar duplicaría el descuento.
    if orden.estado != OrdenMatricula.Estado.PENDIENTE:
        raise ValueError(f"Orden en estado {orden.estado}, no se puede pagar.")

    # --- ORIGEN DE LOS DATOS ---------------------------------------------------------------
    # No se leen los ítems del carro: el carro se vacía en el checkout.
    # El snapshot de la compra vive en la tabla `MatriculaDetalle`, creada en
    # `crear_orden_desde_carro()` con `activa=False` (matrícula "pre-apuntada"
    # pero todavía no oficial). Eso permite:
    #   * congelar precio/nombre/código del curso en el instante del checkout,
    #   * saber exactamente qué cursos hay que descontar al pagar,
    #   * desactivarlas si después la orden se CANCELA.
    #
    # OJO con el filtro: hay que tomar las que están en `activa=False`, es
    # decir, LAS PENDIENTES DE ACTIVAR. Filtrar por `activa=True` aquí sería
    # un error silencioso: como se crearon en False, la consulta vendría
    # vacía, se lanzaría "La orden no tiene matrículas pendientes" y ningún
    # pago podría completarse (el cupo jamás se descontaría).
    matriculas_pendientes = orden.matriculas.select_related('curso').filter(activa=False)
    
    if not matriculas_pendientes.exists():
        raise ValueError("La orden no tiene matrículas pendientes.")

    # 1. BLOQUEAR CURSOS PARA ACTUALIZACIÓN ATÓMICA (SELECT ... FOR UPDATE)
    # ---------------------------------------------------------------------
    # `select_for_update()` traduce a un bloqueo pessimista a nivel de fila
    # sobre el SELECT. Sin esto, dos estudiantes pagando a la vez leerían los
    # MISMOS cupos libres (lectura "fría") y ambos descuentarían sobre la
    # misma cifra -> cupos negativos (overbooking). Con el bloqueo, la segunda
    # transacción espera a que la primera cierre su COMMIT y recién entonces
    # ve los cupos ya restados.
    # `@transaction.atomic` envuelve toda la función: si algo lanza
    # `ValueError`, Django hace ROLLBACK y no queda ni descuento ni orden a
    # medias.
    cursos_ids = matriculas_pendientes.values_list('curso_id', flat=True)
    cursos = Curso.objects.select_for_update().filter(id__in=cursos_ids)

    # 2. VALIDAR CUPOS DISPONIBLES
    # `refresh_from_db()` relee la fila YA bloqueada; usamos `<= 0` (no `< 1`)
    # para que un cupo ya en negativo también rechace el pago.
    cursos_sin_cupo = []
    for matricula in matriculas_pendientes:
        curso = matricula.curso
        # Refrescar desde BD bloqueada
        curso.refresh_from_db()
        if curso.cupos_disponibles <= 0:
            cursos_sin_cupo.append(curso.nombre)

    # 2b. RECHAZO TOTAL: si UN SOLO curso se queda sin cupo, se aborta la
    # operación completa (nunca se descuenta parcialmente).
    if cursos_sin_cupo:
        raise ValueError(
            f"Cupos insuficientes para: {', '.join(cursos_sin_cupo)}. "
            f"Transacción rechazada."
        )

    # 3. DESCONTAR CUPOS Y CONFIRMAR MATRÍCULAS
    # Sólo llegamos aquí si TODOS los cursos tienen cupo. Cada `descontar_cupo()`
    # hace `cupos_disponibles = F('cupos_disponibles') - 1` en SQL (resta en el
    # servidor, no en Python), lo que evita el "lost update".
    for matricula in matriculas_pendientes:
        curso = matricula.curso
        curso.refresh_from_db()  # Asegurar datos frescos

        # Descontar atómicamente
        if not curso.descontar_cupo():
            raise ValueError(f"Error al descontar cupo para {curso.nombre}.")

        # Activar matrícula oficialmente (antes estaba activa=False)
        matricula.activa = True
        matricula.save(update_fields=['activa', 'updated_at'])

    # 4. ACTUALIZAR ORDEN A PAGADO (última escritura dentro de la transacción)
    orden.estado = OrdenMatricula.Estado.PAGADO
    orden.fecha_pago = timezone.now()
    orden.metodo_pago = metodo_pago
    orden.save(update_fields=['estado', 'fecha_pago', 'metodo_pago', 'updated_at'])

    # 5. INVALIDAR EL PREFETCH DE `matriculas`
    # `OrdenMatriculaViewSet.get_queryset()` hace `prefetch_related('matriculas__curso')`.
    # Ese caché se llenó ANTES de activar las matriculas, así que sin este paso
    # el JSON de la respuesta seguiría devolviendo `"activa": false` para una
    # orden recién pagada (confuso para quien la consume, y muy visible en la
    # defensa). Se descarta la caché y DRF vuelve a consultar.
    if hasattr(orden, '_prefetched_objects_cache'):
        orden._prefetched_objects_cache.pop('matriculas', None)

    return orden


@transaction.atomic
def liberar_cupos_orden(orden: OrdenMatricula) -> bool:
    """
    Libera cupos de todos los cursos de una orden cancelada.
    
    CUMPLE PAUTA: "Si la orden es CANCELADA, el cupo del curso se libera 
    automáticamente para que otro estudiante pueda matricularse."
    
    Solo libera si la orden estaba en PAGADO (cupos ya descontados).
    """
    if orden.estado not in [OrdenMatricula.Estado.PAGADO, OrdenMatricula.Estado.PENDIENTE]:
        return False

    # Solo liberar si se habían descontado (estado PAGADO)
    if orden.estado == OrdenMatricula.Estado.PAGADO:
        matriculas = orden.matriculas.select_related('curso').filter(activa=True)
        for matricula in matriculas:
            curso = matricula.curso
            curso.liberar_cupo()
            matricula.activa = False
            matricula.save(update_fields=['activa', 'updated_at'])

    return True


@transaction.atomic
def crear_orden_desde_carro(carro, metodo_pago: str = 'simulado', observaciones: str = '') -> OrdenMatricula:
    """
    Crea la Orden en estado PENDIENTE a partir del carro.

    QUÉ HACE (y qué NO hace):
    1. Valida que el carro no esté vacío y que TODOS los cursos sigan con cupo.
    2. Crea la Orden (registro histórico) con los precios CONGELADOS.
    3. Crea un `MatriculaDetalle` por curso con `activa=False`: es el borrador
       que se confirmará recién al pagar.
    4. Vacía el carro (se "liquida" su contenido, como exige la pauta).

    LO QUE NO HACE: descontar cupos. El cupo se descuenta únicamente en
    `procesar_pago_orden()` cuando la orden pasa a PAGADO. Dejar el checkout
    en PENDIENTE permite que un usuario reserve sin comprometer inventario y
    que el pago se pueda rechazar sin efectos colaterales.

    CUMPLE PAUTA: "Al ejecutar el endpoint de checkout, el contenido del carro
    se liquida y se genera un registro histórico de Orden/Transacción."
    """
    from apps.matriculas.models import ItemCarro
    from apps.usuarios.models import Usuario

    if carro.esta_vacio:
        raise ValueError("El carro está vacío.")

    # Validación informativa previa (la que garantiza la atomicidad está en
    # procesar_pago_orden, porque entre el checkout y el pago otro estudiante
    # puede consumir el último cupo).
    errores = carro.validar_checkout()
    if errores:
        raise ValueError(f"Cupos no disponibles: {errores}")

    items = list(carro.items.select_related('curso').all())
    
    subtotal = sum(item.precio_congelado for item in items)
    total = subtotal

    # Crear orden
    orden = OrdenMatricula.objects.create(
        estudiante=carro.estudiante,
        estado=OrdenMatricula.Estado.PENDIENTE,
        estudiante_nombre=carro.estudiante.get_full_name() or carro.estudiante.username,
        estudiante_email=carro.estudiante.email,
        estudiante_username=carro.estudiante.username,
        subtotal=subtotal,
        total=total,
        metodo_pago=metodo_pago,
        observaciones=observaciones,
    )

    # Crear MatriculaDetalle INACTIVAS (se activan al pagar)
    for item in items:
        MatriculaDetalle.objects.create(
            orden=orden,
            curso=item.curso,
            precio_pagado=item.precio_congelado,
            nombre_curso=item.nombre_congelado,
            codigo_curso=item.codigo_congelado,
            activa=False,  # Se activa al pagar
            fecha_inicio_curso=item.curso.fecha_inicio,
            fecha_fin_curso=item.curso.fecha_fin,
        )

    # Vaciar carro
    carro.limpiar()

    return orden